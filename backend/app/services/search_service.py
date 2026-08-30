from __future__ import annotations

from typing import Any

from sqlalchemy import func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import defer, load_only, noload

from app.models.enums import SequenceType
from app.models.organism import Organism
from app.models.publication import Publication
from app.models.sequence import Sequence
from app.models.source import DataSource
from app.services.pagination import decode_cursor, encode_cursor

_FTS = text("sequences.search_vector @@ websearch_to_tsquery('english', :q)")

# Search/suggest responses never include residues or feature tables.
_SEARCH_LOAD = (
    defer(Sequence.residues),
    noload(Sequence.gene),
    noload(Sequence.dna_feature),
    noload(Sequence.rna_feature),
    noload(Sequence.protein_feature),
    noload(Sequence.crispr_feature),
    noload(Sequence.virus_feature),
    noload(Sequence.protein_domains),
    noload(Sequence.pdb_refs),
    noload(Sequence.cross_references),
    noload(Sequence.references),
)
_SUGGEST_LOAD = (
    load_only(Sequence.id, Sequence.name, Sequence.accession, Sequence.seq_type),
    noload(Sequence.organism),
    noload(Sequence.source),
    noload(Sequence.gene),
    noload(Sequence.dna_feature),
    noload(Sequence.rna_feature),
    noload(Sequence.protein_feature),
    noload(Sequence.crispr_feature),
    noload(Sequence.virus_feature),
    noload(Sequence.protein_domains),
    noload(Sequence.pdb_refs),
    noload(Sequence.cross_references),
    noload(Sequence.references),
)


def _parse_types(types: str | None) -> list[SequenceType]:
    if not types:
        return []
    out = []
    for token in types.split(","):
        token = token.strip().lower()
        try:
            out.append(SequenceType(token))
        except ValueError:
            continue
    return out


async def search(
    session: AsyncSession,
    *,
    q: str,
    types: str | None = None,
    organism: str | None = None,
    source: str | None = None,
    category: str | None = None,
    min_length: int | None = None,
    max_length: int | None = None,
    complexity: str | None = None,
    limit: int = 20,
    cursor: str | None = None,
) -> dict[str, Any]:
    like = f"%{q.strip()}%"
    match = or_(
        _FTS,
        Sequence.name.ilike(like),
        Sequence.accession.ilike(like),
        Sequence.gene_name.ilike(like),
    )
    stmt = select(Sequence).where(match)

    type_list = _parse_types(types or category)
    if type_list:
        stmt = stmt.where(Sequence.seq_type.in_(type_list))
    if organism:
        olike = f"%{organism.strip()}%"
        stmt = stmt.join(Organism, Sequence.organism_id == Organism.id).where(
            or_(
                Organism.scientific_name.ilike(olike),
                Organism.common_name.ilike(olike),
            )
        )
    if source:
        stmt = stmt.join(DataSource, Sequence.source_id == DataSource.id).where(
            DataSource.key == source.strip()
        )
    if min_length is not None:
        stmt = stmt.where(Sequence.length >= min_length)
    if max_length is not None:
        stmt = stmt.where(Sequence.length <= max_length)

    offset = decode_cursor(cursor)
    count_src = stmt.with_only_columns(
        Sequence.id, maintain_column_froms=True
    ).order_by(None)
    total = int(
        (
            await session.execute(
                select(func.count()).select_from(count_src.subquery()).params(q=q)
            )
        ).scalar_one()
    )
    page = (
        stmt.options(*_SEARCH_LOAD)
        .order_by(Sequence.name.asc(), Sequence.id.asc())
        .offset(offset)
        .limit(limit + 1)
        .params(q=q)
    )
    rows = list((await session.execute(page)).scalars().unique().all())
    has_more = len(rows) > limit
    rows = rows[:limit]

    results = [
        {
            "id": str(s.id),
            "accession": s.accession,
            "title": s.name,
            "type": s.seq_type.value,
            "organism": s.organism.scientific_name if s.organism else "",
            "source": s.source.name if s.source else "",
            "length": s.length,
            "category": s.seq_type.value,
        }
        for s in rows
    ]

    publications, pub_total = await _search_publications(session, q)
    try:
        from app.services import paleogenomics_service

        paleo_profiles = await paleogenomics_service.search_profiles(session, q, limit=8)
    except Exception:
        paleo_profiles = []

    return {
        "query": q,
        "total": total,
        "results": results,
        "next_cursor": encode_cursor(offset + limit) if has_more else None,
        "publications": publications,
        "publications_total": pub_total,
        "paleogenomics_profiles": paleo_profiles,
    }


async def _search_publications(session: AsyncSession, q: str, limit: int = 10):
    like = f"%{q.strip()}%"
    # UNION of single-predicate branches lets PostgreSQL use the title/abstract
    # GIN trigram indexes. A single OR with array_to_string() forced a seq scan
    # of every abstract (~110 ms). Same match set, same ordering, same total.
    matched_ids = (
        select(Publication.id)
        .where(Publication.title.ilike(like))
        .union(
            select(Publication.id).where(Publication.abstract.ilike(like)),
            select(Publication.id).where(
                func.array_to_string(Publication.authors, " ").ilike(like)
            ),
        )
        .subquery("matched_pubs")
    )
    stmt = (
        select(Publication, func.count().over().label("total"))
        .options(
            load_only(
                Publication.id,
                Publication.pubmed_id,
                Publication.doi,
                Publication.title,
                Publication.authors,
                Publication.journal,
                Publication.year,
                Publication.url,
            )
        )
        .where(Publication.id.in_(select(matched_ids.c.id)))
        .order_by(Publication.year.desc().nullslast())
        .limit(limit)
    )
    rows = list((await session.execute(stmt)).all())
    if not rows:
        return [], 0
    total = int(rows[0].total)
    pubs = [
        {
            "id": str(p.id),
            "pubmed_id": p.pubmed_id,
            "doi": p.doi,
            "title": p.title,
            "authors": list(p.authors or []),
            "journal": p.journal,
            "year": p.year,
            "url": p.url,
        }
        for p, _total in rows
    ]
    return pubs, total


async def suggest(session: AsyncSession, *, q: str, limit: int = 8) -> dict[str, Any]:
    like = f"{q.strip()}%"
    contains = f"%{q.strip()}%"
    stmt = (
        select(Sequence)
        .options(*_SUGGEST_LOAD)
        .where(or_(Sequence.name.ilike(contains), Sequence.accession.ilike(like)))
        .order_by(Sequence.name.asc())
        .limit(limit)
    )
    rows = list((await session.execute(stmt)).scalars().all())
    try:
        from app.services import paleogenomics_service

        profile_hits = await paleogenomics_service.search_profiles(session, q, limit=min(3, limit))
    except Exception:
        profile_hits = []
    seq_slots = max(0, limit - len(profile_hits))
    rows = rows[:seq_slots]
    suggestions = [
        {
            "id": item["id"],
            "label": f"{item['title']} ({item['scientific_name']})",
            "type": "paleogenomics",
            "slug": item["slug"],
            "accession": None,
        }
        for item in profile_hits
    ]
    suggestions.extend(
        {
            "id": str(s.id),
            "label": s.name,
            "type": s.seq_type.value,
            "accession": s.accession,
        }
        for s in rows
    )
    return {"query": q, "suggestions": suggestions}
