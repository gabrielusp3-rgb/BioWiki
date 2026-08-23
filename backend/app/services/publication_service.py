from __future__ import annotations

from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organism import Organism
from app.models.publication import Publication, SequenceReference
from app.models.sequence import Sequence
from app.services import mappers
from app.services.pagination import decode_cursor, encode_cursor


def _linked_subquery(*, accession: str | None, gene: str | None, organism: str | None):
    sub = select(SequenceReference.publication_id).join(
        Sequence, SequenceReference.sequence_id == Sequence.id
    )
    if accession:
        sub = sub.where(Sequence.accession == accession.strip())
    if gene:
        sub = sub.where(Sequence.gene_name.ilike(f"%{gene.strip()}%"))
    if organism:
        like = f"%{organism.strip()}%"
        sub = sub.join(Organism, Sequence.organism_id == Organism.id).where(
            or_(
                Organism.scientific_name.ilike(like),
                Organism.common_name.ilike(like),
            )
        )
    return sub


async def list_publications(
    session: AsyncSession,
    *,
    q: str | None,
    accession: str | None,
    gene: str | None,
    organism: str | None,
    year: int | None,
    limit: int,
    cursor: str | None,
) -> dict[str, Any]:
    stmt = select(Publication)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(Publication.title.ilike(like), Publication.abstract.ilike(like))
        )
    if year is not None:
        stmt = stmt.where(Publication.year == year)
    if accession or gene or organism:
        stmt = stmt.where(
            Publication.id.in_(
                _linked_subquery(accession=accession, gene=gene, organism=organism)
            )
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
        stmt.order_by(Publication.year.desc().nullslast(), Publication.title.asc())
        .offset(offset)
        .limit(limit + 1)
    )
    rows = list((await session.execute(stmt)).scalars().all())
    has_more = len(rows) > limit
    rows = rows[:limit]
    return {
        "results": [mappers.to_publication(p) for p in rows],
        "total": total,
        "next_cursor": encode_cursor(offset + limit) if has_more else None,
    }


async def get_by_pubmed_id(session: AsyncSession, pubmed_id: int):
    pub = (
        await session.execute(
            select(Publication).where(Publication.pubmed_id == pubmed_id).limit(1)
        )
    ).scalars().first()
    if pub is None:
        return None, []
    accessions = list(
        (
            await session.execute(
                select(Sequence.accession)
                .join(SequenceReference, SequenceReference.sequence_id == Sequence.id)
                .where(SequenceReference.publication_id == pub.id)
                .order_by(Sequence.accession.asc())
            )
        ).scalars().all()
    )
    return pub, accessions
