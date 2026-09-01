from __future__ import annotations

import time

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.models.enums import SequenceType
from app.models.gene import Gene
from app.models.genome import GenomeRecord
from app.models.organism import Organism
from app.models.publication import Publication, SequenceReference
from app.models.sequence import Sequence
from app.schemas.statistics import CategoryStat, StatisticsRead
from app.services import sync_service

# Short in-process TTL. Aggregates only change after ingest; 8s keeps the home
# and category pages from repeating the same COUNT work on every navigation.
_STATS_TTL_SECONDS = 8.0
_stats_cache: tuple[float, StatisticsRead] | None = None


async def get_statistics(session: AsyncSession) -> StatisticsRead:
    global _stats_cache
    now = time.monotonic()
    cached = _stats_cache
    if cached is not None and now - cached[0] < _STATS_TTL_SECONDS:
        return cached[1]
    type_stats = {
        row[0]: (int(row[1]), int(row[2]))
        for row in (
            await session.execute(
                select(
                    Sequence.seq_type,
                    func.count(),
                    func.coalesce(func.sum(Sequence.length), 0),
                ).group_by(Sequence.seq_type)
            )
        ).all()
    }
    category_key = case(
        (Sequence.seq_type == SequenceType.DNA, "dna"),
        (Sequence.seq_type == SequenceType.RNA, "rna"),
        (Sequence.seq_type.in_([SequenceType.PROTEIN, SequenceType.PEPTIDE]), "protein"),
        (Sequence.seq_type == SequenceType.CRISPR, "crispr"),
        (Sequence.seq_type == SequenceType.VIRUS, "virus"),
        else_="other",
    )
    organisms_by_category = {
        str(row[0]): int(row[1])
        for row in (
            await session.execute(
                select(
                    category_key,
                    func.count(func.distinct(Sequence.organism_id)),
                ).group_by(category_key)
            )
        ).all()
    }
    genome_organisms = int(
        (
            await session.execute(
                select(func.count(func.distinct(GenomeRecord.organism_id)))
            )
        ).scalar_one()
    )

    def _for_types(types: list[SequenceType]) -> tuple[int, int]:
        count = 0
        residues = 0
        for seq_type in types:
            n, r = type_stats.get(seq_type, (0, 0))
            count += n
            residues += int(r)
        return count, residues

    total_sequences = sum(n for n, _ in type_stats.values())
    total_residues = sum(int(r) for _, r in type_stats.values())

    organisms, genes, genomes, publications, linked_publications, last_updated = (
        await session.execute(
            select(
                select(func.count()).select_from(Organism).scalar_subquery(),
                select(func.count()).select_from(Gene).scalar_subquery(),
                select(func.count()).select_from(GenomeRecord).scalar_subquery(),
                select(func.count()).select_from(Publication).scalar_subquery(),
                select(
                    func.count(func.distinct(SequenceReference.publication_id))
                ).scalar_subquery(),
                select(func.max(Sequence.updated_at)).scalar_subquery(),
            )
        )
    ).one()

    labels = {
        cat.key: cat.label
        for cat in (
            await session.execute(select(Category).order_by(Category.key))
        ).scalars().all()
    }
    categories: list[CategoryStat] = []
    live_by_key: dict[str, int] = {}
    # Always emit live per-category counts. Do not hide DNA/RNA/protein
    # because the `categories` lookup table was never seeded.
    for key, types in sync_service.CATEGORY_TYPES.items():
        if key == "genome":
            count = int(genomes)
            residues = int(type_stats.get(SequenceType.GENOME, (0, 0))[1])
        else:
            count, residues = _for_types(types)
        live_by_key[key] = count
        categories.append(
            CategoryStat(
                key=key,
                label=labels.get(key) or sync_service.CATEGORY_LABELS[key],
                count=count,
                total_residues=residues,
                distinct_organisms=(
                    genome_organisms if key == "genome" else organisms_by_category.get(key, 0)
                ),
            )
        )

    sync = await sync_service.get_sync_status(
        session,
        total_sequences=total_sequences,
        category_live=live_by_key,
    )

    result = StatisticsRead(
        total_sequences=total_sequences,
        total_residues=int(total_residues),
        organisms=int(organisms),
        genes=int(genes),
        genomes=int(genomes),
        publications=int(publications),
        linked_publications=int(linked_publications),
        categories=categories,
        sync=sync,
        last_updated=last_updated,
    )
    _stats_cache = (now, result)
    return result
