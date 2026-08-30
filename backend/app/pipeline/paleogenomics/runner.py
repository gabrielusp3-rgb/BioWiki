"""Species-oriented Paleogenomics ingest with checkpoint/resume."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_sessionmaker
from app.models.paleogenomics import PaleogenomicProfile, PaleogenomicSequenceMembership
from app.models.publication import Publication
from app.models.sequence import Sequence
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
    classify_record_kind,
    fetch_taxonomy_docs,
    link_publication,
    seed_profiles,
    tag_existing_sequences,
    upsert_claims,
)
from app.pipeline.paleogenomics.semantics import (
    is_complete_mitogenome,
    sequence_length_allowed_for_catalogue,
    sra_run_is_not_a_sequence_accession,
)

logger = get_logger("biowiki.pipeline.paleogenomics")

CHECKPOINT_PATH = Path(__file__).resolve().parents[3] / "data" / "paleogenomics_checkpoint.json"
REPORT_PATH = Path(__file__).resolve().parents[3] / "data" / "paleogenomics_discovery.json"


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
        session.add(
            PaleogenomicSequenceMembership(
                sequence_id=seq.id,
                profile_id=profile.id,
                record_kind=classify_record_kind(seq.name, seq.description),
                is_complete_mitogenome=is_complete_mitogenome(
                    definition=seq.name or seq.description, length=seq.length
                ),
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


async def ingest_literature_for_species(species: PaleogenomicSpecies) -> dict[str, Any]:
    limit = PUBMED_LIMITS.get(species.slug, DEFAULT_PUBMED_LIMIT)
    term = pubmed_term(species)
    search_report = await pubmed.ingest_search(term, limit=limit)
    pmids: set[int] = set()
    for payload in NARRATIVES.get(species.slug) or []:
        for pmid in payload.get("pubmed_ids") or []:
            pmids.add(int(pmid))
    if pmids:
        await pubmed.ingest_pmids(sorted(pmids))
    linked = 0
    async with get_sessionmaker()() as session:
        profile = await _profile_for(session, species.slug)
        pubs = list(
            (
                await session.execute(
                    select(Publication).where(Publication.pubmed_id.in_(sorted(pmids)))
                )
            )
            .scalars()
            .all()
        )
        # Also attach recent search hits matching the scientific name in the title.
        extra = list(
            (
                await session.execute(
                    select(Publication)
                    .where(Publication.title.ilike(f"%{species.scientific_name}%"))
                    .limit(limit)
                )
            )
            .scalars()
            .all()
        )
        for pub in pubs + extra:
            if await link_publication(session, profile, pub):
                linked += 1
        await upsert_claims(session, profile)
        await session.commit()
    return {
        "search_created": search_report.created,
        "search_updated": search_report.updated,
        "linked": linked,
        "term": term,
        "limit": limit,
    }


async def run_paleogenomics(
    *,
    slugs: list[str] | None = None,
    seed_only: bool = False,
    discover_only: bool = False,
    skip_sequences: bool = False,
    skip_genomes: bool = False,
    skip_literature: bool = False,
    checkpoint_path: Path | None = None,
) -> dict[str, Any]:
    path = checkpoint_path or CHECKPOINT_PATH
    checkpoint = load_checkpoint(path)
    chosen = [species_by_slug()[s] for s in slugs] if slugs else list(SPECIES)
    species_report: dict[str, Any] = checkpoint.setdefault("species", {})

    if not job_is_done(checkpoint, "paleo-seed"):
        set_job_status(checkpoint, "paleo-seed", "RUNNING", category="paleogenomics")
        save_checkpoint(path, checkpoint)
        try:
            tax_ids = [row.tax_id for row in SPECIES] + [9606]
            taxonomy = await fetch_taxonomy_docs(tax_ids)
            async with get_sessionmaker()() as session:
                await seed_profiles(session, taxonomy=taxonomy)
                await session.commit()
            set_job_status(checkpoint, "paleo-seed", COMPLETED_SUCCESSFULLY, category="paleogenomics")
            save_checkpoint(path, checkpoint)
        except Exception as exc:
            logger.exception("paleo-seed failed")
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
        return {"checkpoint": str(path), "seed_only": True}

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
