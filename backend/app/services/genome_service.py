from __future__ import annotations

from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import AssemblyLevel
from app.models.genome import GenomeRecord
from app.models.organism import Organism
from app.models.source import DataSource
from app.services import mappers
from app.services.pagination import decode_cursor, encode_cursor


async def list_genomes(
    session: AsyncSession,
    *,
    q: str | None,
    organism: str | None,
    assembly_level: str | None,
    source: str | None,
    limit: int,
    cursor: str | None,
) -> dict[str, Any]:
    stmt = select(GenomeRecord)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                GenomeRecord.accession.ilike(like),
                GenomeRecord.assembly_name.ilike(like),
                GenomeRecord.description.ilike(like),
            )
        )
    if organism:
        like = f"%{organism.strip()}%"
        stmt = stmt.join(Organism, GenomeRecord.organism_id == Organism.id).where(
            or_(
                Organism.scientific_name.ilike(like),
                Organism.common_name.ilike(like),
            )
        )
    if assembly_level:
        try:
            stmt = stmt.where(
                GenomeRecord.assembly_level == AssemblyLevel(assembly_level)
            )
        except ValueError:
            pass
    if source:
        stmt = stmt.join(DataSource, GenomeRecord.source_id == DataSource.id).where(
            DataSource.key == source.strip()
        )

    offset = decode_cursor(cursor)
    total = int(
        (
            await session.execute(
                select(func.count()).select_from(stmt.order_by(None).subquery())
            )
        ).scalar_one()
    )
    stmt = (
        stmt.order_by(GenomeRecord.accession.asc()).offset(offset).limit(limit + 1)
    )
    rows = list((await session.execute(stmt)).scalars().unique().all())
    has_more = len(rows) > limit
    rows = rows[:limit]
    return {
        "results": [mappers.to_genome(g) for g in rows],
        "total": total,
        "next_cursor": encode_cursor(offset + limit) if has_more else None,
    }


async def get_by_accession(
    session: AsyncSession, accession: str
) -> GenomeRecord | None:
    stmt = select(GenomeRecord).where(GenomeRecord.accession == accession).limit(1)
    return (await session.execute(stmt)).scalars().first()
