"""Seed organisms, curated profiles, claims, and introgression rows."""

from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import EvidenceLevel, OrganismGroup, SequenceType
from app.models.organism import Organism
from app.models.paleogenomics import (
    PaleogenomicClaim,
    PaleogenomicClaimSource,
    PaleogenomicIntrogressionRegion,
    PaleogenomicProfile,
    PaleogenomicPublicationMembership,
    PaleogenomicSequenceMembership,
)
from app.models.publication import Publication
from app.models.sequence import Sequence
from app.pipeline.paleogenomics.catalogue import (
    HOMO_SAPIENS_TAX_ID,
    SPECIES,
    PaleogenomicSpecies,
)
from app.pipeline.paleogenomics.introgression import INTROGRESSION_LOCI
from app.pipeline.paleogenomics.narratives import NARRATIVES, REVIEWED
from app.pipeline.paleogenomics.semantics import (
    extract_project_accessions,
    is_complete_mitogenome,
    normalize_doi,
    specimen_label_from_definition,
)
from app.pipeline.taxonomy import group_from_taxonomy, index_taxonomy_for_requested


async def fetch_taxonomy_docs(tax_ids: list[int]) -> dict[int, dict[str, Any]]:
    from app.pipeline.fetchers.base import chunked
    from app.services.connectors.ncbi import NCBIConnector

    lookup: dict[int, dict[str, Any]] = {}
    async with NCBIConnector() as conn:
        for group in chunked([str(t) for t in tax_ids], 40):
            xml = await conn.efetch("taxonomy", list(group), rettype="xml", retmode="xml")
            requested = [int(t) for t in group if str(t).isdigit()]
            lookup.update(index_taxonomy_for_requested(xml, requested))
    return lookup


async def upsert_catalogue_organism(
    session: AsyncSession,
    species: PaleogenomicSpecies,
    tax_doc: dict[str, Any] | None,
) -> Organism:
    existing = (
        await session.execute(select(Organism).where(Organism.tax_id == species.tax_id))
    ).scalar_one_or_none()
    lineage = list((tax_doc or {}).get("lineage") or [])
    group_value = group_from_taxonomy(
        lineage=lineage,
        division=(tax_doc or {}).get("division"),
    ) or OrganismGroup.ANIMAL.value
    rank = (tax_doc or {}).get("rank") or None
    if existing:
        existing.scientific_name = species.scientific_name
        if not existing.common_name:
            existing.common_name = species.common_name
        existing.extinction_status = species.extinction_status.value
        existing.extinction_date_text = species.extinction_date_text
        existing.geologic_period = species.geologic_period
        if lineage:
            existing.lineage = lineage
        if rank:
            existing.rank = rank
        try:
            existing.group = OrganismGroup(group_value)
        except ValueError:
            existing.group = OrganismGroup.ANIMAL
        return existing

    slug = species.slug
    clash = (await session.execute(select(Organism).where(Organism.slug == slug))).scalar_one_or_none()
    if clash:
        slug = f"{slug}-{species.tax_id}"
    organism = Organism(
        slug=slug[:160],
        scientific_name=species.scientific_name,
        common_name=species.common_name,
        tax_id=species.tax_id,
        rank=rank,
        lineage=lineage or None,
        group=OrganismGroup(group_value) if group_value in OrganismGroup._value2member_map_ else OrganismGroup.ANIMAL,
        extinction_status=species.extinction_status.value,
        extinction_date_text=species.extinction_date_text,
        geologic_period=species.geologic_period,
    )
    session.add(organism)
    await session.flush()
    return organism


async def upsert_profile(
    session: AsyncSession,
    species: PaleogenomicSpecies,
    organism: Organism,
) -> PaleogenomicProfile:
    existing = (
        await session.execute(select(PaleogenomicProfile).where(PaleogenomicProfile.slug == species.slug))
    ).scalar_one_or_none()
    if existing is None:
        existing = (
            await session.execute(
                select(PaleogenomicProfile).where(PaleogenomicProfile.organism_id == organism.id)
            )
        ).scalar_one_or_none()
    if existing is None:
        existing = PaleogenomicProfile(slug=species.slug, organism_id=organism.id)
        session.add(existing)
    existing.organism_id = organism.id
    existing.slug = species.slug
    existing.common_name = species.common_name
    existing.geographic_region = species.geographic_region
    existing.subsection = species.subsection.value
    existing.featured_rank = species.featured_rank
    existing.deextinction_status = species.deextinction_status.value
    existing.last_reviewed_on = REVIEWED
    existing.taxonomic_uncertainty = species.taxonomic_uncertainty
    await session.flush()
    return existing


async def upsert_claims(session: AsyncSession, profile: PaleogenomicProfile) -> None:
    rows = NARRATIVES.get(profile.slug) or []
    for payload in rows:
        section_key = str(payload["section_key"])
        claim = (
            await session.execute(
                select(PaleogenomicClaim).where(
                    PaleogenomicClaim.profile_id == profile.id,
                    PaleogenomicClaim.section_key == section_key,
                )
            )
        ).scalar_one_or_none()
        if claim is None:
            claim = PaleogenomicClaim(profile_id=profile.id, section_key=section_key)
            session.add(claim)
        claim.title = str(payload["title"])
        claim.body = str(payload["body"])
        level = str(payload["evidence_level"])
        EvidenceLevel(level)
        claim.evidence_level = level
        claim.sort_order = int(payload["sort_order"])
        reviewed = payload.get("last_reviewed_on")
        claim.last_reviewed_on = date.fromisoformat(str(reviewed)) if reviewed else REVIEWED
        await session.flush()

        wanted: list[tuple[int | None, str | None, str | None]] = []
        for pmid in payload.get("pubmed_ids") or []:
            wanted.append((int(pmid), None, None))
        for doi in payload.get("dois") or []:
            wanted.append((None, normalize_doi(str(doi)), None))
        for url in payload.get("urls") or []:
            wanted.append((None, None, str(url).strip() or None))

        existing_sources = list(
            (
                await session.execute(
                    select(PaleogenomicClaimSource).where(
                        PaleogenomicClaimSource.claim_id == claim.id
                    )
                )
            )
            .scalars()
            .all()
        )
        have = {
            (s.pubmed_id, normalize_doi(s.doi), s.url) for s in existing_sources
        }
        for pmid, doi, url in wanted:
            if pmid is None and doi is None and not url:
                continue
            key = (pmid, doi, url)
            if key in have:
                continue
            publication_id = None
            if pmid:
                pub = (
                    await session.execute(select(Publication).where(Publication.pubmed_id == pmid))
                ).scalar_one_or_none()
                if pub:
                    publication_id = pub.id
            elif doi:
                pub = (
                    await session.execute(select(Publication).where(Publication.doi == doi))
                ).scalar_one_or_none()
                if pub:
                    publication_id = pub.id
            session.add(
                PaleogenomicClaimSource(
                    claim_id=claim.id,
                    publication_id=publication_id,
                    pubmed_id=pmid,
                    doi=doi,
                    url=url,
                )
            )
            have.add(key)


async def ensure_homo_sapiens(session: AsyncSession, tax_doc: dict[str, Any] | None) -> Organism:
    existing = (
        await session.execute(select(Organism).where(Organism.tax_id == HOMO_SAPIENS_TAX_ID))
    ).scalar_one_or_none()
    if existing:
        return existing
    lineage = list((tax_doc or {}).get("lineage") or [])
    group_value = group_from_taxonomy(
        lineage=lineage, division=(tax_doc or {}).get("division")
    ) or OrganismGroup.ANIMAL.value
    organism = Organism(
        slug="homo-sapiens",
        scientific_name="Homo sapiens",
        common_name="human",
        tax_id=HOMO_SAPIENS_TAX_ID,
        rank=(tax_doc or {}).get("rank") or "species",
        lineage=lineage or None,
        group=OrganismGroup(group_value) if group_value in OrganismGroup._value2member_map_ else OrganismGroup.ANIMAL,
    )
    clash = (
        await session.execute(select(Organism).where(Organism.slug == organism.slug))
    ).scalar_one_or_none()
    if clash:
        organism.slug = f"homo-sapiens-{HOMO_SAPIENS_TAX_ID}"
    session.add(organism)
    await session.flush()
    return organism


async def upsert_introgression(session: AsyncSession, modern: Organism) -> int:
    created = 0
    for row in INTROGRESSION_LOCI:
        gene = str(row["gene_name"])
        source = str(row["archaic_source"])
        existing = (
            await session.execute(
                select(PaleogenomicIntrogressionRegion).where(
                    PaleogenomicIntrogressionRegion.archaic_source == source,
                    PaleogenomicIntrogressionRegion.gene_name == gene,
                    PaleogenomicIntrogressionRegion.start_position.is_(None),
                )
            )
        ).scalar_one_or_none()
        pubmed_id = int(row["pubmed_id"]) if row.get("pubmed_id") else None
        publication_id = None
        if pubmed_id:
            pub = (
                await session.execute(select(Publication).where(Publication.pubmed_id == pubmed_id))
            ).scalar_one_or_none()
            if pub:
                publication_id = pub.id
        if existing is None:
            existing = PaleogenomicIntrogressionRegion(
                modern_organism_id=modern.id,
                archaic_source=source,
                gene_name=gene,
                evidence_notes=str(row["evidence_notes"]),
            )
            session.add(existing)
            created += 1
        existing.locus_name = str(row.get("locus_name") or "") or None
        existing.pubmed_id = pubmed_id
        existing.publication_id = publication_id
        existing.method = str(row.get("method") or "") or None
        existing.evidence_notes = str(row["evidence_notes"])
        existing.source_dataset = str(row.get("source_dataset") or "") or None
        existing.modern_organism_id = modern.id
    await session.flush()
    return created


def classify_record_kind(name: str | None, description: str | None) -> str:
    text = f"{name or ''} {description or ''}".lower()
    if "mitochond" in text or "mitogenome" in text or "mtdna" in text:
        return "mitochondrial"
    if "chromosome" in text or "nuclear genome" in text:
        return "nuclear"
    if "gene" in text or "cds" in text:
        return "gene"
    return "other"


async def tag_existing_sequences(session: AsyncSession, profile: PaleogenomicProfile) -> int:
    tagged = 0
    rows = list(
        (
            await session.execute(
                select(Sequence).where(
                    Sequence.organism_id == profile.organism_id,
                    Sequence.seq_type.in_(
                        [SequenceType.DNA, SequenceType.RNA, SequenceType.PROTEIN]
                    ),
                )
            )
        )
        .scalars()
        .all()
    )
    for seq in rows:
        existing = (
            await session.execute(
                select(PaleogenomicSequenceMembership).where(
                    PaleogenomicSequenceMembership.sequence_id == seq.id
                )
            )
        ).scalar_one_or_none()
        if existing:
            continue
        kind = classify_record_kind(seq.name, seq.description)
        complete = is_complete_mitogenome(definition=seq.name or seq.description, length=seq.length)
        projects, samples = extract_project_accessions(seq.name, seq.description, seq.source_url)
        session.add(
            PaleogenomicSequenceMembership(
                sequence_id=seq.id,
                profile_id=profile.id,
                record_kind=kind,
                is_complete_mitogenome=complete,
                specimen_label=specimen_label_from_definition(seq.name, seq.description),
                biosample=samples[0] if samples else None,
                bioproject=projects[0] if projects else None,
            )
        )
        tagged += 1
    if tagged:
        profile.paleogenomic_data_available = True
    await session.flush()
    return tagged


async def retag_complete_mitogenome_flags(session: AsyncSession) -> int:
    """Recompute complete-mitogenome flags from stored definition + length."""
    updated = 0
    rows = (
        await session.execute(
            select(PaleogenomicSequenceMembership, Sequence).join(
                Sequence, Sequence.id == PaleogenomicSequenceMembership.sequence_id
            )
        )
    ).all()
    for membership, seq in rows:
        flag = is_complete_mitogenome(
            definition=seq.name or seq.description, length=seq.length
        )
        if membership.is_complete_mitogenome != flag:
            membership.is_complete_mitogenome = flag
            updated += 1
    await session.flush()
    return updated


async def backfill_membership_source_metadata(session: AsyncSession) -> int:
    """Fill specimen/BioSample/BioProject only when the stored record states them."""
    updated = 0
    rows = (
        await session.execute(
            select(PaleogenomicSequenceMembership, Sequence).join(
                Sequence, Sequence.id == PaleogenomicSequenceMembership.sequence_id
            )
        )
    ).all()
    for membership, seq in rows:
        changed = False
        if not membership.specimen_label:
            label = specimen_label_from_definition(seq.name, seq.description)
            if label:
                membership.specimen_label = label
                changed = True
        projects, samples = extract_project_accessions(seq.name, seq.description, seq.source_url)
        if not membership.bioproject and projects:
            membership.bioproject = projects[0]
            changed = True
        if not membership.biosample and samples:
            membership.biosample = samples[0]
            changed = True
        if changed:
            updated += 1
    await session.flush()
    return updated


async def link_publication(
    session: AsyncSession, profile: PaleogenomicProfile, publication: Publication
) -> bool:
    existing = (
        await session.execute(
            select(PaleogenomicPublicationMembership).where(
                PaleogenomicPublicationMembership.profile_id == profile.id,
                PaleogenomicPublicationMembership.publication_id == publication.id,
            )
        )
    ).scalar_one_or_none()
    if existing:
        return False
    session.add(
        PaleogenomicPublicationMembership(profile_id=profile.id, publication_id=publication.id)
    )
    return True


async def seed_profiles(session: AsyncSession, *, taxonomy: dict[int, dict[str, Any]] | None = None) -> dict[str, str]:
    taxonomy = taxonomy or {}
    mapping: dict[str, str] = {}
    for species in SPECIES:
        organism = await upsert_catalogue_organism(session, species, taxonomy.get(species.tax_id))
        profile = await upsert_profile(session, species, organism)
        await upsert_claims(session, profile)
        mapping[species.slug] = str(profile.id)
    sapiens = await ensure_homo_sapiens(session, taxonomy.get(HOMO_SAPIENS_TAX_ID))
    await upsert_introgression(session, sapiens)
    await backfill_membership_source_metadata(session)
    await session.flush()
    return mapping
