"""Idempotent persistence of real bibliographic records.

Publications are deduplicated by their strongest verifiable identifier, in
order: PubMed ID, then DOI, then exact title. Records with no identifier and
no title are rejected — nothing is fabricated to fill the gap.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.publication import Publication
from app.pipeline.models import ParsedPublication


def _clean_year(year: int | None) -> int | None:
    if year is None:
        return None
    return year if 1800 <= year <= 2100 else None


def _clip(value: str | None, max_len: int) -> str | None:
    if value is None:
        return None
    text = value.strip()
    if not text:
        return None
    return text if len(text) <= max_len else text[:max_len]


async def upsert_publication(
    session: AsyncSession, parsed: ParsedPublication
) -> Publication | None:
    """Insert or update a publication; returns None for unidentifiable records.

    A real title is mandatory (it is NOT NULL in the schema and is never
    synthesised). Untitled references can be completed later via the PubMed
    fetcher, which retrieves the actual bibliographic record.
    """
    if not (parsed.title and parsed.title.strip()):
        return None

    existing: Publication | None = None
    if parsed.pubmed_id:
        existing = (
            await session.execute(
                select(Publication).where(Publication.pubmed_id == parsed.pubmed_id)
            )
        ).scalar_one_or_none()
    if existing is None and parsed.doi:
        existing = (
            await session.execute(
                select(Publication).where(Publication.doi == parsed.doi)
            )
        ).scalar_one_or_none()
    if existing is None and parsed.title and not parsed.pubmed_id and not parsed.doi:
        existing = (
            await session.execute(
                select(Publication).where(Publication.title == parsed.title.strip())
            )
        ).scalar_one_or_none()

    if existing is not None:
        # Fill gaps with real values from the newer record; never overwrite
        # a populated field with None.
        if parsed.title and not existing.title:
            existing.title = parsed.title.strip()
        if parsed.abstract and not existing.abstract:
            existing.abstract = parsed.abstract
        if parsed.doi and not existing.doi:
            existing.doi = _clip(parsed.doi, 255)
        if parsed.pmc_id and not existing.pmc_id:
            existing.pmc_id = _clip(parsed.pmc_id, 32)
        if parsed.authors and not existing.authors:
            existing.authors = parsed.authors
        if parsed.journal and not existing.journal:
            existing.journal = _clip(parsed.journal, 300)
        if _clean_year(parsed.year) and not existing.year:
            existing.year = _clean_year(parsed.year)
        if parsed.volume and not existing.volume:
            existing.volume = _clip(parsed.volume, 32)
        if parsed.pages and not existing.pages:
            existing.pages = _clip(parsed.pages, 64)
        if parsed.url and not existing.url:
            existing.url = _clip(parsed.url, 500)
        return existing

    publication = Publication(
        pubmed_id=parsed.pubmed_id,
        doi=_clip(parsed.doi, 255),
        pmc_id=_clip(parsed.pmc_id, 32),
        title=parsed.title.strip(),
        abstract=parsed.abstract,
        authors=parsed.authors or None,
        journal=_clip(parsed.journal, 300),
        year=_clean_year(parsed.year),
        volume=_clip(parsed.volume, 32),
        pages=_clip(parsed.pages, 64),
        url=_clip(parsed.url, 500),
    )
    session.add(publication)
    await session.flush()
    return publication
