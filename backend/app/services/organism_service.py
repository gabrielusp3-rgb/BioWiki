from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import OrganismGroup
from app.models.organism import Organism
from app.services import mappers, paleogenomics_service
from app.services.pagination import decode_cursor, encode_cursor


async def _with_paleo_slugs(session: AsyncSession, rows: list[Organism]) -> list:
    slugs = await paleogenomics_service.slugs_by_organism_ids(
        session, [row.id for row in rows]
    )
    return [mappers.to_organism(row, paleogenomic_slug=slugs.get(row.id)) for row in rows]


async def list_organisms(
    session: AsyncSession, *, group: str | None, limit: int, cursor: str | None
) -> dict[str, Any]:
    stmt = select(Organism)
    if group:
        try:
            stmt = stmt.where(Organism.group == OrganismGroup(group))
        except ValueError:
            pass
    offset = decode_cursor(cursor)
    total = int(
        (await session.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()
    )
    stmt = stmt.order_by(Organism.scientific_name.asc()).offset(offset).limit(limit + 1)
    rows = list((await session.execute(stmt)).scalars().all())
    has_more = len(rows) > limit
    rows = rows[:limit]
    return {
        "organisms": await _with_paleo_slugs(session, rows),
        "total": total,
        "next_cursor": encode_cursor(offset + limit) if has_more else None,
    }


async def featured(session: AsyncSession, *, limit: int) -> dict[str, Any]:
    stmt = (
        select(Organism)
        .where(Organism.sequence_count.isnot(None), Organism.sequence_count > 0)
        .order_by(Organism.sequence_count.desc().nullslast())
        .limit(limit)
    )
    rows = list((await session.execute(stmt)).scalars().all())
    return {
        "organisms": await _with_paleo_slugs(session, rows),
        "total": len(rows),
        "next_cursor": None,
    }


async def get_by_identifier(
    session: AsyncSession, identifier: str
) -> Organism | None:
    ident = identifier.strip()
    conditions = [Organism.slug == ident.lower()]
    if ident.isdigit():
        conditions.append(Organism.tax_id == int(ident))
    try:
        conditions.append(Organism.id == uuid.UUID(ident))
    except ValueError:
        pass
    stmt = select(Organism).where(or_(*conditions)).limit(1)
    return (await session.execute(stmt)).scalars().first()
