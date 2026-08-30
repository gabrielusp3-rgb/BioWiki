"""Species-oriented Paleogenomics ingest with checkpoint/resume."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_sessionmaker
from app.models.paleogenomics import (
    PaleogenomicProfile,
    PaleogenomicProject,
    PaleogenomicSequenceMembership,
)
from app.models.publication import Publication
from app.models.sequence import Sequence
from app.services.connectors.ncbi import NCBIConnector
from app.pipeline.expansion.checkpoint import (
    COMPLETED_SUCCESSFULLY,
    TEMPORARY_FAILURE,
    job_is_done,
    load_checkpoint,
    save_checkpoint,
    set_job_status,
)
from app.pipeline.fetchers import datasets, ncbi, pubmed
from app.pipeline.fetchers.base import import_with_run
from app.pipeline.importers.genome_importer import GenomeImporter
from app.pipeline.logging import get_logger
from app.pipeline.paleogenomics.catalogue import (
    DEFAULT_PUBMED_LIMIT,
    GENOME_ASSEMBLY_LIMIT,
    PUBMED_LIMITS,
    SPECIES,
    PaleogenomicSpecies,
    species_by_slug,
)
from app.pipeline.paleogenomics.discover import discover_accessions
from app.pipeline.paleogenomics.narratives import NARRATIVES
from app.pipeline.paleogenomics.seed import (
    backfill_membership_source_metadata,
    classify_record_kind,
    fetch_taxonomy_docs,
    link_publication,
    seed_profiles,
    tag_existing_sequences,
    upsert_claims,
    retag_complete_mitogenome_flags,
)
from app.pipeline.paleogenomics.semantics import (
    extract_project_accessions,
    is_complete_mitogenome,
    sequence_length_allowed_for_catalogue,
    specimen_label_from_definition,
    species_search_names,
    sra_run_is_not_a_sequence_accession,
)

logger = get_logger("biowiki.pipeline.paleogenomics")

CHECKPOINT_PATH = Path(__file__).resolve().parents[3] / "data" / "paleogenomics_checkpoint.json"
REPORT_PATH = Path(__file__).resolve().parents[3] / "data" / "paleogenomics_discovery.json"
BIOPROJECT_LIMIT = 12


def pubmed_term(species: PaleogenomicSpecies) -> str:
    names = [species.scientific_name, species.common_name, *species.synonyms]
    name_clause = " OR ".join(f'"{n}"[Title/Abstract]' for n in names if n)
    return (
        f"({name_clause}) AND "
        "(DNA OR genome OR ancient OR extinction OR paleogenom* OR mitochondrial "
        "OR phylogen* OR ecology)"
    )


async def _profile_for(session: AsyncSession, slug: str) -> PaleogenomicProfile:
    profile = (
        await session.execute(select(PaleogenomicProfile).where(PaleogenomicProfile.slug == slug))
    ).scalar_one()
    return profile


async def _membership_count(session: AsyncSession, profile_id) -> int:
    from sqlalchemy import func

    return int(
        (
            await session.execute(
                select(func.count()).where(PaleogenomicSequenceMembership.profile_id == profile_id)
            )
        ).scalar_one()
    )


async def _tag_parsed(
    session: AsyncSession,
    profile: PaleogenomicProfile,
    accessions: list[str],
) -> int:
    tagged = 0
    if not accessions:
        return 0
    rows = list(
        (
            await session.execute(select(Sequence).where(Sequence.accession.in_(accessions)))
        )
        .scalars()
        .all()
    )
    for seq in rows:
        if seq.organism_id != profile.organism_id:
            continue
        exists = (
            await session.execute(
                select(PaleogenomicSequenceMembership.id).where(
                    PaleogenomicSequenceMembership.sequence_id == seq.id
                )
            )
        ).scalar_one_or_none()
        if exists:
            continue
        projects, samples = extract_project_accessions(seq.name, seq.description, seq.source_url)
        session.add(
            PaleogenomicSequenceMembership(
                sequence_id=seq.id,
                profile_id=profile.id,
                record_kind=classify_record_kind(seq.name, seq.description),
                is_complete_mitogenome=is_complete_mitogenome(
                    definition=seq.name or seq.description, length=seq.length
                ),
                specimen_label=specimen_label_from_definition(seq.name, seq.description),
                biosample=samples[0] if samples else None,
                bioproject=projects[0] if projects else None,
            )
        )
        tagged += 1
    if tagged:
        profile.paleogenomic_data_available = True
    return tagged


async def ingest_sequences_for_species(
    species: PaleogenomicSpecies,
    *,
    db: str,
    keep: int,
    molecule: str,
) -> dict[str, Any]:
    if keep <= 0:
        return {"created": 0, "updated": 0, "skipped": 0, "discovery": {"accessions": []}}
    discovery = await discover_accessions(
        species,
        db=db,
        search_limit=min(400, max(keep * 4, 40)),
        keep=keep,
        molecule=molecule,
    )
    accessions = list(discovery.get("accessions") or [])
    parsed = []
    if accessions:
        parsed = await ncbi.fetch_records(accessions, db=db, seq_type="protein" if db == "protein" else "dna")
    kept = []
    skipped_reasons: list[str] = []
    for ps in parsed:
        if sra_run_is_not_a_sequence_accession(ps.accession):
            skipped_reasons.append(f"{ps.accession}:sra")
            continue
        if not ps.organism or ps.organism.tax_id != species.tax_id:
            skipped_reasons.append(f"{ps.accession}:tax_mismatch")
            continue
        length = ps.effective_length()
        if not sequence_length_allowed_for_catalogue(length, molecule=molecule):
            skipped_reasons.append(f"{ps.accession}:length")
            continue
        if not ps.residues:
            skipped_reasons.append(f"{ps.accession}:no_residues")
            continue
        kept.append(ps)
    report = await import_with_run(
        kept,
        source_key="ncbi",
        kind=f"paleo-{species.slug}-{db}",
        params={"tax_id": species.tax_id, "db": db, "kept": len(kept)},
        batch_size=40,
    )
    async with get_sessionmaker()() as session:
        profile = await _profile_for(session, species.slug)
        tagged = await _tag_parsed(session, profile, [ps.accession for ps in kept])
        await session.commit()
    return {
        "created": report.created,
        "updated": report.updated,
        "skipped": report.skipped + len(skipped_reasons),
        "failed": report.failed,
        "discovery": discovery,
        "skipped_reasons": skipped_reasons[:40],
        "tagged": tagged,
    }


async def ingest_remaining_sequences_for_species(
    species: PaleogenomicSpecies,
    *,
    current: int,
) -> dict[str, Any]:
    """Additive nuccore fill after a completed job, still bounded by the discovery goal.

    Does not reset the original nuccore checkpoint. Already-tagged accessions are skipped.
    """
    remaining = max(0, species.preferred_sequence_target - current)
    if remaining <= 0:
        return {"created": 0, "reason": "at_or_above_target"}
    keep = min(400, max(species.preferred_sequence_target, current + remaining))
    discovery = await discover_accessions(
        species,
        db="nuccore",
        search_limit=min(400, max(species.preferred_sequence_target * 4, 40)),
        keep=keep,
        molecule="dna",
        dedupe_titles=False,
    )
    accessions = list(discovery.get("accessions") or [])
    async with get_sessionmaker()() as session:
        profile = await _profile_for(session, species.slug)
        already = set(
            (
                await session.execute(
                    select(Sequence.accession)
                    .join(
                        PaleogenomicSequenceMembership,
                        PaleogenomicSequenceMembership.sequence_id == Sequence.id,
                    )
                    .where(PaleogenomicSequenceMembership.profile_id == profile.id)
                )
            )
            .scalars()
            .all()
        )
    new_accessions = [acc for acc in accessions if acc not in already][:remaining]
    if not new_accessions:
        return {
            "created": 0,
            "reason": "source_exhausted",
            "discovery_hits": discovery.get("total_hits"),
            "already_tagged": len(already),
            "discovery": {"term": discovery.get("term"), "total_hits": discovery.get("total_hits")},
        }
    parsed = await ncbi.fetch_records(new_accessions, db="nuccore", seq_type="dna")
    kept = []
    skipped_reasons: list[str] = []
    for ps in parsed:
        if sra_run_is_not_a_sequence_accession(ps.accession):
            skipped_reasons.append(f"{ps.accession}:sra")
            continue
        if not ps.organism or ps.organism.tax_id != species.tax_id:
            skipped_reasons.append(f"{ps.accession}:tax_mismatch")
            continue
        length = ps.effective_length()
        if not sequence_length_allowed_for_catalogue(length, molecule="dna"):
            skipped_reasons.append(f"{ps.accession}:length")
            continue
        if not ps.residues:
            skipped_reasons.append(f"{ps.accession}:no_residues")
            continue
        kept.append(ps)
    report = await import_with_run(
        kept,
        source_key="ncbi",
        kind=f"paleo-{species.slug}-nuccore-remainder",
        params={"tax_id": species.tax_id, "db": "nuccore", "kept": len(kept)},
        batch_size=40,
    )
    async with get_sessionmaker()() as session:
        profile = await _profile_for(session, species.slug)
        tagged = await _tag_parsed(session, profile, [ps.accession for ps in kept])
        await session.commit()
    return {
        "created": report.created,
        "updated": report.updated,
        "skipped": report.skipped + len(skipped_reasons),
        "failed": report.failed,
        "tagged": tagged,
        "reason": "remainder",
        "new_accessions": [ps.accession for ps in kept],
        "discovery_hits": discovery.get("total_hits"),
        "skipped_reasons": skipped_reasons[:40],
    }


async def ingest_genomes_for_species(species: PaleogenomicSpecies) -> dict[str, Any]:
    genomes = await datasets.fetch_reports(taxon=str(species.tax_id), limit=GENOME_ASSEMBLY_LIMIT)
    kept = [
        g
        for g in genomes
        if g.organism and g.organism.tax_id == species.tax_id
    ]
    created = updated = skipped = failed = 0
    async with get_sessionmaker()() as session:
        importer = GenomeImporter(session)
        for genome in kept:
            try:
                async with session.begin_nested():
                    _, was_created = await importer.upsert_genome(genome)
                if was_created:
                    created += 1
                else:
                    updated += 1
            except Exception as exc:  # noqa: BLE001
                failed += 1
                logger.exception("paleo genome %s: %s", genome.accession, exc)
        profile = await _profile_for(session, species.slug)
        if created or updated:
            profile.paleogenomic_data_available = True
        await session.commit()
    return {
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "failed": failed,
        "accessions": [g.accession for g in kept],
    }


def _literature_limit(species: PaleogenomicSpecies) -> int:
    return PUBMED_LIMITS.get(species.slug, DEFAULT_PUBMED_LIMIT)


def _narrative_pmids(species: PaleogenomicSpecies) -> set[int]:
    pmids: set[int] = set()
    for payload in NARRATIVES.get(species.slug) or []:
        for pmid in payload.get("pubmed_ids") or []:
            pmids.add(int(pmid))
    return pmids


def _publication_name_filter(species: PaleogenomicSpecies):
    clauses = []
    for name in species_search_names(
        species.scientific_name, species.common_name, species.synonyms
    ):
        like = f"%{name}%"
        clauses.append(Publication.title.ilike(like))
        clauses.append(Publication.abstract.ilike(like))
    return or_(*clauses) if clauses else Publication.id.is_(None)


async def _publications_for_profile(
    session: AsyncSession,
    species: PaleogenomicSpecies,
    pmids: set[int],
    *,
    limit: int,
) -> list[Publication]:
    found: dict[object, Publication] = {}
    if pmids:
        for pub in (
            await session.execute(select(Publication).where(Publication.pubmed_id.in_(sorted(pmids))))
        ).scalars():
            found[pub.id] = pub
    remaining = max(0, limit - len(found))
    if remaining:
        extra = list(
            (
                await session.execute(
                    select(Publication)
                    .where(_publication_name_filter(species))
                    .order_by(Publication.year.desc().nullslast())
                    .limit(remaining + len(found))
                )
            )
            .scalars()
            .all()
        )
        for pub in extra:
            if pub.id in found:
                continue
            found[pub.id] = pub
            if len(found) >= limit:
                break
    return list(found.values())


async def ingest_literature_for_species(species: PaleogenomicSpecies) -> dict[str, Any]:
    limit = _literature_limit(species)
    term = pubmed_term(species)
    search_pmids = set(await pubmed.search_pmids(term, limit=limit))
    pmids = set(search_pmids) | _narrative_pmids(species)
    search_report = await pubmed.ingest_pmids(sorted(pmids)) if pmids else None
    linked = 0
    async with get_sessionmaker()() as session:
        profile = await _profile_for(session, species.slug)
        pubs = await _publications_for_profile(session, species, pmids, limit=limit)
        for pub in pubs:
            if await link_publication(session, profile, pub):
                linked += 1
        await upsert_claims(session, profile)
        await session.commit()
    return {
        "search_created": 0 if search_report is None else search_report.created,
        "search_updated": 0 if search_report is None else search_report.updated,
        "linked": linked,
        "term": term,
        "limit": limit,
        "search_pmids": len(search_pmids),
    }


async def relink_literature_for_species(species: PaleogenomicSpecies) -> dict[str, Any]:
    """Attach already-stored publications using names and curated PMIDs. No new NCBI fetch."""
    limit = _literature_limit(species)
    linked = 0
    async with get_sessionmaker()() as session:
        profile = await _profile_for(session, species.slug)
        pubs = await _publications_for_profile(
            session, species, _narrative_pmids(species), limit=limit
        )
        for pub in pubs:
            if await link_publication(session, profile, pub):
                linked += 1
        await upsert_claims(session, profile)
        await session.commit()
    return {"slug": species.slug, "linked": linked, "limit": limit}


async def _upsert_project(
    session: AsyncSession,
    profile: PaleogenomicProfile,
    *,
    bioproject: str | None,
    biosample: str | None = None,
    notes: str | None = None,
    library_strategy: str | None = None,
    source_url: str | None = None,
    controlled_access: bool = False,
) -> bool:
    if not bioproject and not biosample:
        return False
    stmt = select(PaleogenomicProject).where(PaleogenomicProject.profile_id == profile.id)
    if bioproject:
        stmt = stmt.where(PaleogenomicProject.bioproject == bioproject)
    elif biosample:
        stmt = stmt.where(PaleogenomicProject.biosample == biosample)
    existing = (await session.execute(stmt.limit(1))).scalar_one_or_none()
    if existing is None:
        session.add(
            PaleogenomicProject(
                profile_id=profile.id,
                bioproject=bioproject,
                biosample=biosample,
                notes=notes,
                library_strategy=library_strategy,
                source_url=source_url,
                controlled_access=controlled_access,
            )
        )
        return True
    if notes and not existing.notes:
        existing.notes = notes
    if library_strategy and not existing.library_strategy:
        existing.library_strategy = library_strategy
    if source_url and not existing.source_url:
        existing.source_url = source_url
    if biosample and not existing.biosample:
        existing.biosample = biosample
    return False


async def ingest_bioprojects_for_species(species: PaleogenomicSpecies) -> dict[str, Any]:
    """Store public BioProject metadata. Does not import SRA reads as Sequence rows."""
    created = 0
    updated = 0
    async with NCBIConnector() as conn:
        page = await conn.esearch(
            "bioproject",
            f"txid{species.tax_id}[Organism:noexp]",
            retmax=BIOPROJECT_LIMIT,
        )
        uids = [hit.identifier for hit in page.hits if hit.identifier]
        payload = await conn.esummary("bioproject", uids) if uids else {"result": {}}
    result = payload.get("result") or {}
    rows: list[dict[str, Any]] = []
    for uid in result.get("uids") or uids:
        rec = result.get(str(uid))
        if isinstance(rec, dict):
            rows.append(rec)
    async with get_sessionmaker()() as session:
        profile = await _profile_for(session, species.slug)
        for rec in rows:
            acc = str(rec.get("project_acc") or "").strip().upper()
            if not acc.startswith("PRJ"):
                continue
            title = str(rec.get("project_title") or rec.get("project_name") or "").strip()
            data_type = str(rec.get("project_data_type") or "").strip()
            note_bits = [part for part in (title, data_type) if part]
            was_new = await _upsert_project(
                session,
                profile,
                bioproject=acc,
                notes=" — ".join(note_bits)[:500] or None,
                library_strategy=data_type or None,
                source_url=f"https://www.ncbi.nlm.nih.gov/bioproject/{acc}",
            )
            if was_new:
                created += 1
            else:
                updated += 1
        members = list(
            (
                await session.execute(
                    select(Sequence.name, Sequence.description, Sequence.annotations).where(
                        Sequence.id.in_(
                            select(PaleogenomicSequenceMembership.sequence_id).where(
                                PaleogenomicSequenceMembership.profile_id == profile.id
                            )
                        )
                    )
                )
            ).all()
        )
        for name, description, annotations in members:
            extra = ""
            if isinstance(annotations, dict):
                extra = " ".join(str(v) for v in annotations.values() if isinstance(v, str))
            projects, samples = extract_project_accessions(name, description, extra)
            for acc in projects[:4]:
                if await _upsert_project(
                    session,
                    profile,
                    bioproject=acc,
                    source_url=f"https://www.ncbi.nlm.nih.gov/bioproject/{acc}",
                    notes="Accession recorded on a stored GenBank/INSDC sequence record.",
                ):
                    created += 1
                else:
                    updated += 1
            for sample in samples[:4]:
                if await _upsert_project(
                    session,
                    profile,
                    biosample=sample,
                    source_url=f"https://www.ncbi.nlm.nih.gov/biosample/{sample}",
                    notes="BioSample recorded on a stored sequence record. Raw reads are not imported.",
                ):
                    created += 1
                else:
                    updated += 1
        if created or updated:
            profile.paleogenomic_data_available = True
        await session.commit()
    return {
        "slug": species.slug,
        "bioproject_hits": page.total,
        "created": created,
        "updated": updated,
        "stored": created + updated,
    }


async def run_paleogenomics(
    *,
    slugs: list[str] | None = None,
    seed_only: bool = False,
    discover_only: bool = False,
    skip_sequences: bool = False,
    skip_genomes: bool = False,
    skip_literature: bool = False,
    relink_literature: bool = False,
    ingest_projects: bool = False,
    checkpoint_path: Path | None = None,
) -> dict[str, Any]:
    path = checkpoint_path or CHECKPOINT_PATH
    checkpoint = load_checkpoint(path)
    chosen = [species_by_slug()[s] for s in slugs] if slugs else list(SPECIES)
    species_report: dict[str, Any] = checkpoint.setdefault("species", {})

    if seed_only or not job_is_done(checkpoint, "paleo-seed"):
        if not seed_only:
            set_job_status(checkpoint, "paleo-seed", "RUNNING", category="paleogenomics")
            save_checkpoint(path, checkpoint)
        try:
            tax_ids = [row.tax_id for row in SPECIES] + [9606]
            taxonomy = await fetch_taxonomy_docs(tax_ids)
            async with get_sessionmaker()() as session:
                await seed_profiles(session, taxonomy=taxonomy)
                await session.commit()
            if not job_is_done(checkpoint, "paleo-seed"):
                set_job_status(
                    checkpoint, "paleo-seed", COMPLETED_SUCCESSFULLY, category="paleogenomics"
                )
            save_checkpoint(path, checkpoint)
        except Exception as exc:
            logger.exception("paleo-seed failed")
            if not seed_only:
                set_job_status(
                    checkpoint,
                    "paleo-seed",
                    TEMPORARY_FAILURE,
                    category="paleogenomics",
                    reason=str(exc)[:300],
                )
                save_checkpoint(path, checkpoint)
            raise

    if seed_only:
        return {"checkpoint": str(path), "seed_only": True, "upserted": True}

    if relink_literature or ingest_projects:
        out: dict[str, Any] = {"checkpoint": str(path), "species": {}}
        for species in chosen:
            slug = species.slug
            bucket: dict[str, Any] = {}
            if ingest_projects:
                job = f"paleo-{slug}-projects"
                if not job_is_done(checkpoint, job):
                    set_job_status(checkpoint, job, "RUNNING", category="paleogenomics")
                    save_checkpoint(path, checkpoint)
                    try:
                        bucket["projects"] = await ingest_bioprojects_for_species(species)
                        set_job_status(
                            checkpoint,
                            job,
                            COMPLETED_SUCCESSFULLY,
                            category="paleogenomics",
                            records_created=int(bucket["projects"].get("created") or 0),
                        )
                    except Exception as exc:
                        logger.exception("%s failed", job)
                        set_job_status(
                            checkpoint, job, TEMPORARY_FAILURE, reason=str(exc)[:300]
                        )
                    save_checkpoint(path, checkpoint)
                else:
                    bucket["projects"] = {"skipped": "already_done"}
            if relink_literature:
                bucket["relink"] = await relink_literature_for_species(species)
            out["species"][slug] = bucket
        async with get_sessionmaker()() as session:
            out["mitogenome_flags_updated"] = await retag_complete_mitogenome_flags(session)
            out["membership_metadata_updated"] = await backfill_membership_source_metadata(session)
            await session.commit()
        save_checkpoint(path, checkpoint)
        return out

    discovery_out: dict[str, Any] = {}
    for species in chosen:
        slug = species.slug
        bucket = species_report.setdefault(slug, {})
        async with get_sessionmaker()() as session:
            profile = await _profile_for(session, slug)
            tagged_existing = await tag_existing_sequences(session, profile)
            current = await _membership_count(session, profile.id)
            await session.commit()
        bucket["tagged_existing"] = tagged_existing
        bucket["current_sequences"] = current
        remaining = max(0, species.preferred_sequence_target - current)

        nuc_job = f"paleo-{slug}-nuccore"
        prot_job = f"paleo-{slug}-protein"
        if discover_only or not skip_sequences:
            nuc_keep = remaining
            prot_keep = min(max(0, remaining // 5), 20) if remaining else 0
            nuc_disc = await discover_accessions(
                species,
                db="nuccore",
                search_limit=min(400, max(species.preferred_sequence_target * 3, 40)),
                keep=max(nuc_keep, 8),
                molecule="dna",
            )
            prot_disc = await discover_accessions(
                species,
                db="protein",
                search_limit=min(120, max(prot_keep * 3, 20)),
                keep=max(prot_keep, 4),
                molecule="protein",
            )
            bucket["discovery"] = {
                "target": species.preferred_sequence_target,
                "current": current,
                "remaining": remaining,
                "nuccore_hits": nuc_disc.get("total_hits"),
                "nuccore_kept": len(nuc_disc.get("accessions") or []),
                "protein_hits": prot_disc.get("total_hits"),
                "protein_kept": len(prot_disc.get("accessions") or []),
                "tax_id": species.tax_id,
            }
            discovery_out[slug] = bucket["discovery"]
            if discover_only:
                save_checkpoint(path, checkpoint)
                continue
            if not skip_sequences and not job_is_done(checkpoint, nuc_job) and nuc_keep:
                set_job_status(checkpoint, nuc_job, "RUNNING", category="paleogenomics")
                save_checkpoint(path, checkpoint)
                try:
                    result = await ingest_sequences_for_species(
                        species, db="nuccore", keep=nuc_keep, molecule="dna"
                    )
                    bucket["nuccore"] = result
                    set_job_status(
                        checkpoint,
                        nuc_job,
                        COMPLETED_SUCCESSFULLY,
                        category="paleogenomics",
                        records_created=int(result.get("created") or 0),
                    )
                except Exception as exc:
                    logger.exception("%s failed", nuc_job)
                    set_job_status(
                        checkpoint, nuc_job, TEMPORARY_FAILURE, reason=str(exc)[:300]
                    )
                save_checkpoint(path, checkpoint)
            if not skip_sequences and not job_is_done(checkpoint, prot_job) and prot_keep:
                set_job_status(checkpoint, prot_job, "RUNNING", category="paleogenomics")
                save_checkpoint(path, checkpoint)
                try:
                    result = await ingest_sequences_for_species(
                        species, db="protein", keep=prot_keep, molecule="protein"
                    )
                    bucket["protein"] = result
                    set_job_status(
                        checkpoint,
                        prot_job,
                        COMPLETED_SUCCESSFULLY,
                        category="paleogenomics",
                        records_created=int(result.get("created") or 0),
                    )
                except Exception as exc:
                    logger.exception("%s failed", prot_job)
                    set_job_status(
                        checkpoint, prot_job, TEMPORARY_FAILURE, reason=str(exc)[:300]
                    )
                save_checkpoint(path, checkpoint)

        remainder_job = f"paleo-{slug}-nuccore-remainder"
        if (
            not discover_only
            and not skip_sequences
            and remaining > 0
            and job_is_done(checkpoint, nuc_job)
            and not job_is_done(checkpoint, remainder_job)
        ):
            set_job_status(checkpoint, remainder_job, "RUNNING", category="paleogenomics")
            save_checkpoint(path, checkpoint)
            try:
                remainder = await ingest_remaining_sequences_for_species(
                    species, current=current
                )
                bucket["nuccore_remainder"] = remainder
                set_job_status(
                    checkpoint,
                    remainder_job,
                    COMPLETED_SUCCESSFULLY,
                    category="paleogenomics",
                    records_created=int(remainder.get("created") or 0),
                    reason=str(remainder.get("reason") or "")[:300] or None,
                )
            except Exception as exc:
                logger.exception("%s failed", remainder_job)
                set_job_status(
                    checkpoint, remainder_job, TEMPORARY_FAILURE, reason=str(exc)[:300]
                )
            save_checkpoint(path, checkpoint)
            async with get_sessionmaker()() as session:
                profile = await _profile_for(session, slug)
                current = await _membership_count(session, profile.id)
            remaining = max(0, species.preferred_sequence_target - current)
            bucket["current_sequences"] = current
            bucket["remaining"] = remaining

        genome_job = f"paleo-{slug}-genomes"
        if not discover_only and not skip_genomes and not job_is_done(checkpoint, genome_job):
            set_job_status(checkpoint, genome_job, "RUNNING", category="paleogenomics")
            save_checkpoint(path, checkpoint)
            try:
                bucket["genomes"] = await ingest_genomes_for_species(species)
                set_job_status(checkpoint, genome_job, COMPLETED_SUCCESSFULLY, category="paleogenomics")
            except Exception as exc:
                logger.exception("%s failed", genome_job)
                set_job_status(checkpoint, genome_job, TEMPORARY_FAILURE, reason=str(exc)[:300])
            save_checkpoint(path, checkpoint)

        lit_job = f"paleo-{slug}-pubmed"
        if not discover_only and not skip_literature and not job_is_done(checkpoint, lit_job):
            set_job_status(checkpoint, lit_job, "RUNNING", category="paleogenomics")
            save_checkpoint(path, checkpoint)
            try:
                bucket["literature"] = await ingest_literature_for_species(species)
                set_job_status(checkpoint, lit_job, COMPLETED_SUCCESSFULLY, category="paleogenomics")
            except Exception as exc:
                logger.exception("%s failed", lit_job)
                set_job_status(checkpoint, lit_job, TEMPORARY_FAILURE, reason=str(exc)[:300])
            save_checkpoint(path, checkpoint)

        proj_job = f"paleo-{slug}-projects"
        if not discover_only and not job_is_done(checkpoint, proj_job):
            set_job_status(checkpoint, proj_job, "RUNNING", category="paleogenomics")
            save_checkpoint(path, checkpoint)
            try:
                bucket["projects"] = await ingest_bioprojects_for_species(species)
                set_job_status(
                    checkpoint,
                    proj_job,
                    COMPLETED_SUCCESSFULLY,
                    category="paleogenomics",
                    records_created=int((bucket.get("projects") or {}).get("created") or 0),
                )
            except Exception as exc:
                logger.exception("%s failed", proj_job)
                set_job_status(checkpoint, proj_job, TEMPORARY_FAILURE, reason=str(exc)[:300])
            save_checkpoint(path, checkpoint)

        async with get_sessionmaker()() as session:
            profile = await _profile_for(session, slug)
            bucket["final_sequences"] = await _membership_count(session, profile.id)
        save_checkpoint(path, checkpoint)

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps({"species": discovery_out or species_report}, indent=2, default=str),
        encoding="utf-8",
    )
    checkpoint["report_path"] = str(REPORT_PATH)
    save_checkpoint(path, checkpoint)
    return {"checkpoint": str(path), "report": str(REPORT_PATH), "species": species_report}
