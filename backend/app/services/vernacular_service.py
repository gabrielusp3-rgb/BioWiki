"""Read verified vernacular names. Does not invent a translation."""

from __future__ import annotations

import uuid
from typing import Any

from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vernacular import OrganismVernacularName
from app.schemas.organism import OrganismRead
from app.pipeline.paleogenomics.vernacular import locale_or_none, resolve_display


async def vernacular_fields(
    session: AsyncSession,
    organism_id: uuid.UUID | None,
    *,
    locale: str | None,
    english_name: str | None,
    scientific_name: str,
) -> dict[str, Any]:
    empty = {
        "localized_common_name": None,
        "localized_common_name_locale": None,
        "vernacular_source": None,
        "vernacular_source_url": None,
        "vernacular_fallback": False,
    }
    chosen = locale_or_none(locale)
    if chosen is None or organism_id is None:
        return empty
    rows = (
        await session.execute(
            select(OrganismVernacularName).where(OrganismVernacularName.organism_id == organism_id)
        )
    ).scalars().all()
    by_locale = {
        row.locale: {
            "name": row.name,
            "locale": row.locale,
            "source": row.source,
            "source_url": row.source_url or "",
        }
        for row in rows
    }
    resolved = resolve_display(
        chosen,
        by_locale,
        english_name=english_name,
        scientific_name=scientific_name,
    )
    if resolved is None:
        return empty
    return _fields_from_resolved(resolved)


def _fields_from_resolved(resolved: dict[str, Any] | None) -> dict[str, Any]:
    if resolved is None:
        return {
            "localized_common_name": None,
            "localized_common_name_locale": None,
            "vernacular_source": None,
            "vernacular_source_url": None,
            "vernacular_fallback": False,
        }
    return {
        "localized_common_name": resolved["name"],
        "localized_common_name_locale": resolved["locale"],
        "vernacular_source": resolved.get("source") or None,
        "vernacular_source_url": resolved.get("source_url") or None,
        "vernacular_fallback": bool(resolved["fallback"]),
    }


async def attach_localized_names(
    session: AsyncSession,
    organisms: list[OrganismRead],
    locale: str | None,
) -> list[OrganismRead]:
    """One query for the whole page. Does not invent a name."""
    chosen = locale_or_none(locale)
    if chosen is None or not organisms:
        return organisms
    ids = [item.id for item in organisms]
    rows = (
        await session.execute(
            select(OrganismVernacularName).where(OrganismVernacularName.organism_id.in_(ids))
        )
    ).scalars().all()
    grouped: dict[uuid.UUID, dict[str, dict[str, str]]] = defaultdict(dict)
    for row in rows:
        grouped[row.organism_id][row.locale] = {
            "name": row.name,
            "locale": row.locale,
            "source": row.source,
            "source_url": row.source_url or "",
        }
    attached: list[OrganismRead] = []
    for item in organisms:
        resolved = resolve_display(
            chosen,
            grouped.get(item.id, {}),
            english_name=item.common_name,
            scientific_name=item.scientific_name,
        )
        attached.append(item.model_copy(update=_fields_from_resolved(resolved)))
    return attached
