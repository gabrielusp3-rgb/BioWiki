"""Paleogenomics collection queries. Counts are live; never hardcoded."""

from __future__ import annotations

from typing import Any

from sqlalchemy import exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import SequenceType
from app.models.genome import GenomeRecord
from app.models.organism import Organism
from app.models.paleogenomics import (
    PaleogenomicIntrogressionRegion,
    PaleogenomicProfile,
    PaleogenomicProject,
    PaleogenomicPublicationMembership,
    PaleogenomicSequenceMembership,
)
from app.models.publication import Publication
from app.models.sequence import Sequence
from app.schemas.paleogenomics import (
    PaleogenomicClaimRead,
    PaleogenomicClaimSourceRead,
    PaleogenomicIntrogressionRead,
    PaleogenomicOverview,
    PaleogenomicProjectRead,
    PaleogenomicSequenceRow,
    PaleogenomicSpeciesCard,
)
from app.services import mappers
from app.services.pagination import decode_cursor, encode_cursor

_NO_DNA_NOTES = [
    "Homo floresiensis, Homo naledi and Homo erectus are not listed as palaeogenomic "
    "sequence taxa here because authentic public ancient DNA for those species is not "
    "established in this catalogue. Absence of a page is not a claim about fossils.",
    "Introgression regions in living Homo sapiens are not ancient specimen DNA.",
]


def _preferred_sequence_target(slug: str) -> int:
    """Optional catalogue metadata. Must not break API import if pipeline is absent."""
    try:
        from app.pipeline.paleogenomics.catalogue import species_by_slug

        row = species_by_slug().get(slug)
        return int(row.preferred_sequence_target) if row else 0
    except Exception:
        return 0


async def _count_map(session: AsyncSession, stmt) -> dict:
    return {row[0]: int(row[1]) for row in (await session.execute(stmt)).all()}


async def _profile_counts(session: AsyncSession) -> dict[str, dict[str, int]]:
    seq_counts = await _count_map(
        session,
        select(PaleogenomicSequenceMembership.profile_id, func.count()).group_by(
            PaleogenomicSequenceMembership.profile_id
        ),
    )
    mt_counts = await _count_map(
        session,
        select(PaleogenomicSequenceMembership.profile_id, func.count())
        .where(PaleogenomicSequenceMembership.is_complete_mitogenome.is_(True))
        .group_by(PaleogenomicSequenceMembership.profile_id),
    )
    pub_counts = await _count_map(
        session,
        select(PaleogenomicPublicationMembership.profile_id, func.count()).group_by(
            PaleogenomicPublicationMembership.profile_id
        ),
    )
    project_counts = await _count_map(
        session,
        select(PaleogenomicProject.profile_id, func.count()).group_by(PaleogenomicProject.profile_id),
    )
    assembly_counts = await _count_map(
        session,
        select(PaleogenomicProfile.id, func.count())
        .join(Organism, Organism.id == PaleogenomicProfile.organism_id)
        .join(GenomeRecord, GenomeRecord.organism_id == Organism.id)
        .group_by(PaleogenomicProfile.id),
    )
    return {
        "sequences": seq_counts,
        "mitogenomes": mt_counts,
        "publications": pub_counts,
        "projects": project_counts,
        "assemblies": assembly_counts,
    }


def _card(profile: PaleogenomicProfile, counts: dict[str, dict[str, int]]) -> PaleogenomicSpeciesCard:
    org = profile.organism
    return PaleogenomicSpeciesCard(
        slug=profile.slug,
        common_name=profile.common_name,
        scientific_name=org.scientific_name if org else profile.common_name,
        tax_id=org.tax_id if org else 0,
        subsection=profile.subsection,
        extinction_status=org.extinction_status if org else None,
        extinction_date_text=org.extinction_date_text if org else None,
        geologic_period=org.geologic_period if org else None,
        geographic_region=profile.geographic_region,
        featured_rank=profile.featured_rank,
        deextinction_status=profile.deextinction_status,
        paleogenomic_data_available=profile.paleogenomic_data_available,
        taxonomic_uncertainty=profile.taxonomic_uncertainty,
        sequence_count=counts["sequences"].get(profile.id, 0),
        assembly_count=counts["assemblies"].get(profile.id, 0),
        publication_count=counts["publications"].get(profile.id, 0),
        mitogenome_count=counts["mitogenomes"].get(profile.id, 0),
    )


async def overview_stats(session: AsyncSession) -> PaleogenomicOverview:
    species_count = int(
        (await session.execute(select(func.count()).select_from(PaleogenomicProfile))).scalar_one()
    )
    archaic = int(
        (
            await session.execute(
                select(func.count()).where(PaleogenomicProfile.subsection == "archaic_hominin")
            )
        ).scalar_one()
    )
    sequences = int(
        (
            await session.execute(select(func.count()).select_from(PaleogenomicSequenceMembership))
        ).scalar_one()
    )
    publications = int(
        (
            await session.execute(
                select(func.count()).select_from(PaleogenomicPublicationMembership)
            )
        ).scalar_one()
    )
    introgression = int(
        (
            await session.execute(select(func.count()).select_from(PaleogenomicIntrogressionRegion))
        ).scalar_one()
    )
    projects = int(
        (await session.execute(select(func.count()).select_from(PaleogenomicProject))).scalar_one()
    )
    assemblies = int(
        (
            await session.execute(
                select(func.count(func.distinct(GenomeRecord.id)))
                .select_from(GenomeRecord)
                .join(PaleogenomicProfile, PaleogenomicProfile.organism_id == GenomeRecord.organism_id)
            )
        ).scalar_one()
    )
    last = (
        await session.execute(select(func.max(PaleogenomicProfile.last_reviewed_on)))
    ).scalar_one()
    return PaleogenomicOverview(
        species_count=species_count,
        archaic_hominin_count=archaic,
        extinct_species_count=max(0, species_count - archaic),
        sequence_count=sequences,
        assembly_count=assemblies,
        publication_count=publications,
        introgression_count=introgression,
        project_count=projects,
        last_reviewed_on=last,
    )


async def landing(session: AsyncSession) -> dict[str, Any]:
    counts = await _profile_counts(session)
    profiles = list(
        (await session.execute(select(PaleogenomicProfile).order_by(PaleogenomicProfile.common_name)))
        .scalars()
        .all()
    )
    cards = [_card(p, counts) for p in profiles]
    featured = sorted(
        [c for c in cards if c.featured_rank is not None],
        key=lambda c: c.featured_rank or 99,
    )
    return {
        "overview": await overview_stats(session),
        "featured": featured,
        "species": cards,
        "notes": _NO_DNA_NOTES,
    }


def _apply_filters(stmt, *, q, subsection, extinction_status, geographic_region, deextinction, dna_available, assembly_available):
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                PaleogenomicProfile.common_name.ilike(like),
                PaleogenomicProfile.slug.ilike(like),
                Organism.scientific_name.ilike(like),
                Organism.common_name.ilike(like),
            )
        )
    if subsection:
        stmt = stmt.where(PaleogenomicProfile.subsection == subsection)
    if extinction_status:
        stmt = stmt.where(Organism.extinction_status == extinction_status)
    if geographic_region:
        stmt = stmt.where(PaleogenomicProfile.geographic_region.ilike(f"%{geographic_region.strip()}%"))
    if deextinction:
        stmt = stmt.where(PaleogenomicProfile.deextinction_status == deextinction)
    if dna_available is True:
        stmt = stmt.where(PaleogenomicProfile.paleogenomic_data_available.is_(True))
    if dna_available is False:
        stmt = stmt.where(PaleogenomicProfile.paleogenomic_data_available.is_(False))
    if assembly_available is True:
        stmt = stmt.where(
            exists().where(GenomeRecord.organism_id == PaleogenomicProfile.organism_id)
        )
    elif assembly_available is False:
        stmt = stmt.where(
            ~exists().where(GenomeRecord.organism_id == PaleogenomicProfile.organism_id)
        )
    return stmt


async def list_species(
    session: AsyncSession,
    *,
    q: str | None,
    subsection: str | None,
    extinction_status: str | None,
    geographic_region: str | None,
    deextinction: str | None,
    dna_available: bool | None,
    assembly_available: bool | None,
    limit: int,
    cursor: str | None,
) -> dict[str, Any]:
    stmt = select(PaleogenomicProfile).join(Organism, Organism.id == PaleogenomicProfile.organism_id)
    stmt = _apply_filters(
        stmt,
        q=q,
        subsection=subsection,
        extinction_status=extinction_status,
        geographic_region=geographic_region,
        deextinction=deextinction,
        dna_available=dna_available,
        assembly_available=assembly_available,
    )
    counts = await _profile_counts(session)
    offset = decode_cursor(cursor)
    total = int(
        (
            await session.execute(select(func.count()).select_from(stmt.order_by(None).subquery()))
        ).scalar_one()
    )
    rows = list(
        (
            await session.execute(
                stmt.order_by(PaleogenomicProfile.common_name.asc()).offset(offset).limit(limit + 1)
            )
        )
        .scalars()
        .unique()
        .all()
    )
    has_more = len(rows) > limit
    rows = rows[:limit]
    cards = [_card(p, counts) for p in rows]
    return {
        "results": cards,
        "total": total,
        "next_cursor": encode_cursor(offset + limit) if has_more else None,
    }


async def get_species(session: AsyncSession, slug: str) -> dict[str, Any] | None:
    profile = (
        await session.execute(select(PaleogenomicProfile).where(PaleogenomicProfile.slug == slug))
    ).scalar_one_or_none()
    if profile is None:
        return None
    counts = await _profile_counts(session)
    card = _card(profile, counts)
    claims = [
        PaleogenomicClaimRead(
            section_key=c.section_key,
            title=c.title,
            body=c.body,
            evidence_level=c.evidence_level,
            sort_order=c.sort_order,
            last_reviewed_on=c.last_reviewed_on,
            sources=[
                PaleogenomicClaimSourceRead(
                    pubmed_id=s.pubmed_id,
                    doi=s.doi,
                    url=s.url,
                    label=s.label,
                    publication_id=s.publication_id,
                )
                for s in c.sources
            ],
        )
        for c in profile.claims
    ]
    intro_count = None
    intro_note = None
    if profile.subsection == "archaic_hominin":
        source = "neanderthal" if "neanderthal" in slug else "denisovan" if "denisova" in slug else None
        if source:
            intro_count = int(
                (
                    await session.execute(
                        select(func.count()).where(
                            PaleogenomicIntrogressionRegion.archaic_source == source
                        )
                    )
                ).scalar_one()
            )
            intro_note = (
                "Introgression counts describe ancestry in living Homo sapiens, not DNA "
                "extracted from this archaic specimen."
            )
    org = profile.organism
    return {
        "slug": profile.slug,
        "common_name": profile.common_name,
        "scientific_name": org.scientific_name if org else profile.common_name,
        "tax_id": org.tax_id if org else 0,
        "subsection": profile.subsection,
        "organism": mappers.to_organism(org, paleogenomic_slug=profile.slug) if org else None,
        "extinction_status": org.extinction_status if org else None,
        "extinction_date_text": org.extinction_date_text if org else None,
        "geologic_period": org.geologic_period if org else None,
        "geographic_region": profile.geographic_region,
        "deextinction_status": profile.deextinction_status,
        "paleogenomic_data_available": profile.paleogenomic_data_available,
        "taxonomic_uncertainty": profile.taxonomic_uncertainty,
        "last_reviewed_on": profile.last_reviewed_on,
        "preferred_sequence_target": _preferred_sequence_target(profile.slug),
        "sequence_count": card.sequence_count,
        "assembly_count": card.assembly_count,
        "publication_count": card.publication_count,
        "mitogenome_count": card.mitogenome_count,
        "project_count": counts["projects"].get(profile.id, 0),
        "claims": claims,
        "introgression_count": intro_count,
        "introgression_note": intro_note,
    }


async def list_sequences(
    session: AsyncSession, slug: str, *, limit: int, cursor: str | None
) -> dict[str, Any] | None:
    profile = (
        await session.execute(select(PaleogenomicProfile.id).where(PaleogenomicProfile.slug == slug))
    ).scalar_one_or_none()
    if profile is None:
        return None
    stmt = (
        select(Sequence, PaleogenomicSequenceMembership)
        .join(
            PaleogenomicSequenceMembership,
            PaleogenomicSequenceMembership.sequence_id == Sequence.id,
        )
        .where(PaleogenomicSequenceMembership.profile_id == profile)
        .where(Sequence.seq_type != SequenceType.GENOME)
    )
    offset = decode_cursor(cursor)
    total = int(
        (await session.execute(select(func.count()).select_from(stmt.order_by(None).subquery()))).scalar_one()
    )
    rows = list(
        (
            await session.execute(
                stmt.order_by(Sequence.accession.asc()).offset(offset).limit(limit + 1)
            )
        ).all()
    )
    has_more = len(rows) > limit
    rows = rows[:limit]
    results = [
        PaleogenomicSequenceRow(
            id=seq.id,
            accession=seq.accession,
            name=seq.name,
            seq_type=seq.seq_type.value,
            length=seq.length,
            record_kind=mem.record_kind,
            is_complete_mitogenome=mem.is_complete_mitogenome,
            specimen_label=mem.specimen_label,
            biosample=mem.biosample,
            bioproject=mem.bioproject,
            source_url=seq.source_url,
        )
        for seq, mem in rows
    ]
    return {
        "results": results,
        "total": total,
        "next_cursor": encode_cursor(offset + limit) if has_more else None,
    }


async def list_publications(
    session: AsyncSession, slug: str, *, limit: int, cursor: str | None
) -> dict[str, Any] | None:
    profile = (
        await session.execute(select(PaleogenomicProfile.id).where(PaleogenomicProfile.slug == slug))
    ).scalar_one_or_none()
    if profile is None:
        return None
    stmt = (
        select(Publication)
        .join(
            PaleogenomicPublicationMembership,
            PaleogenomicPublicationMembership.publication_id == Publication.id,
        )
        .where(PaleogenomicPublicationMembership.profile_id == profile)
    )
    offset = decode_cursor(cursor)
    total = int(
        (await session.execute(select(func.count()).select_from(stmt.order_by(None).subquery()))).scalar_one()
    )
    rows = list(
        (
            await session.execute(
                stmt.order_by(Publication.year.desc().nullslast(), Publication.title.asc())
                .offset(offset)
                .limit(limit + 1)
            )
        )
        .scalars()
        .all()
    )
    has_more = len(rows) > limit
    rows = rows[:limit]
    return {
        "results": [mappers.to_publication(p) for p in rows],
        "total": total,
        "next_cursor": encode_cursor(offset + limit) if has_more else None,
    }


async def list_genomes(
    session: AsyncSession, slug: str, *, limit: int, cursor: str | None
) -> dict[str, Any] | None:
    profile = (
        await session.execute(select(PaleogenomicProfile).where(PaleogenomicProfile.slug == slug))
    ).scalar_one_or_none()
    if profile is None:
        return None
    stmt = select(GenomeRecord).where(GenomeRecord.organism_id == profile.organism_id)
    offset = decode_cursor(cursor)
    total = int(
        (await session.execute(select(func.count()).select_from(stmt.order_by(None).subquery()))).scalar_one()
    )
    rows = list(
        (
            await session.execute(
                stmt.order_by(GenomeRecord.accession.asc()).offset(offset).limit(limit + 1)
            )
        )
        .scalars()
        .all()
    )
    has_more = len(rows) > limit
    rows = rows[:limit]
    return {
        "results": [mappers.to_genome(g) for g in rows],
        "total": total,
        "next_cursor": encode_cursor(offset + limit) if has_more else None,
    }


async def list_projects(
    session: AsyncSession, slug: str, *, limit: int, cursor: str | None
) -> dict[str, Any] | None:
    profile = (
        await session.execute(select(PaleogenomicProfile.id).where(PaleogenomicProfile.slug == slug))
    ).scalar_one_or_none()
    if profile is None:
        return None
    stmt = select(PaleogenomicProject).where(PaleogenomicProject.profile_id == profile)
    offset = decode_cursor(cursor)
    total = int(
        (await session.execute(select(func.count()).select_from(stmt.order_by(None).subquery()))).scalar_one()
    )
    rows = list(
        (
            await session.execute(
                stmt.order_by(PaleogenomicProject.bioproject.asc().nullslast())
                .offset(offset)
                .limit(limit + 1)
            )
        )
        .scalars()
        .all()
    )
    has_more = len(rows) > limit
    rows = rows[:limit]
    return {
        "results": [
            PaleogenomicProjectRead(
                bioproject=p.bioproject,
                biosample=p.biosample,
                run_accession=p.run_accession,
                experiment_accession=p.experiment_accession,
                library_strategy=p.library_strategy,
                source_url=p.source_url,
                notes=p.notes,
                controlled_access=p.controlled_access,
            )
            for p in rows
        ],
        "total": total,
        "next_cursor": encode_cursor(offset + limit) if has_more else None,
    }


INTROGRESSION_NOTE = (
    "These records describe ancestry intervals or gene-level associations in living "
    "Homo sapiens. They are not DNA extracted from archaic bones. Coordinates are "
    "included only when a cited paper and genome build are stored; gene-level rows "
    "are otherwise incomplete by design."
)


async def list_introgression(
    session: AsyncSession,
    *,
    archaic_source: str | None,
    limit: int,
    cursor: str | None,
) -> dict[str, Any]:
    stmt = select(PaleogenomicIntrogressionRegion)
    if archaic_source:
        stmt = stmt.where(PaleogenomicIntrogressionRegion.archaic_source == archaic_source)
    offset = decode_cursor(cursor)
    total = int(
        (await session.execute(select(func.count()).select_from(stmt.order_by(None).subquery()))).scalar_one()
    )
    rows = list(
        (
            await session.execute(
                stmt.order_by(
                    PaleogenomicIntrogressionRegion.archaic_source.asc(),
                    PaleogenomicIntrogressionRegion.gene_name.asc(),
                )
                .offset(offset)
                .limit(limit + 1)
            )
        )
        .scalars()
        .all()
    )
    has_more = len(rows) > limit
    rows = rows[:limit]
    results = [
        PaleogenomicIntrogressionRead(
            id=row.id,
            archaic_source=row.archaic_source,
            gene_name=row.gene_name,
            locus_name=row.locus_name,
            reference_build=row.reference_build,
            chromosome=row.chromosome,
            start_position=row.start_position,
            end_position=row.end_position,
            pubmed_id=row.pubmed_id,
            doi=row.doi,
            method=row.method,
            evidence_notes=row.evidence_notes,
            source_dataset=row.source_dataset,
            modern_scientific_name=(
                row.modern_organism.scientific_name if row.modern_organism else "Homo sapiens"
            ),
        )
        for row in rows
    ]
    return {
        "results": results,
        "total": total,
        "next_cursor": encode_cursor(offset + limit) if has_more else None,
        "note": INTROGRESSION_NOTE,
    }


async def search_profiles(session: AsyncSession, q: str, *, limit: int = 8) -> list[dict[str, Any]]:
    like = f"%{q.strip()}%"
    rows = list(
        (
            await session.execute(
                select(PaleogenomicProfile)
                .join(Organism, Organism.id == PaleogenomicProfile.organism_id)
                .where(
                    or_(
                        PaleogenomicProfile.common_name.ilike(like),
                        PaleogenomicProfile.slug.ilike(like),
                        Organism.scientific_name.ilike(like),
                        Organism.common_name.ilike(like),
                    )
                )
                .order_by(PaleogenomicProfile.common_name.asc())
                .limit(limit)
            )
        )
        .scalars()
        .unique()
        .all()
    )
    return [
        {
            "id": str(p.id),
            "slug": p.slug,
            "title": p.common_name,
            "scientific_name": p.organism.scientific_name if p.organism else p.common_name,
            "type": "paleogenomics",
        }
        for p in rows
    ]


async def slugs_by_organism_ids(
    session: AsyncSession, organism_ids: list
) -> dict:
    if not organism_ids:
        return {}
    rows = (
        await session.execute(
            select(PaleogenomicProfile.organism_id, PaleogenomicProfile.slug).where(
                PaleogenomicProfile.organism_id.in_(organism_ids)
            )
        )
    ).all()
    return {row[0]: row[1] for row in rows}
