from __future__ import annotations

import uuid

from app.models.enums import OrganismGroup
from app.schemas.common import CamelModel


class OrganismRead(CamelModel):
    id: uuid.UUID
    slug: str
    scientific_name: str
    common_name: str | None = None
    tax_id: int
    rank: str | None = None
    lineage: list[str] = []
    group: OrganismGroup
    image_url: str | None = None
    sequence_count: int | None = None
    extinction_status: str | None = None
    extinction_date_text: str | None = None
    geologic_period: str | None = None
    paleogenomic_slug: str | None = None
    localized_common_name: str | None = None
    localized_common_name_locale: str | None = None
    vernacular_source: str | None = None
    vernacular_source_url: str | None = None
    vernacular_fallback: bool = False


class OrganismListResponse(CamelModel):
    organisms: list[OrganismRead]
    total: int
    next_cursor: str | None = None
