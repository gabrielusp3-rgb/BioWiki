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


class OrganismListResponse(CamelModel):
    organisms: list[OrganismRead]
    total: int
    next_cursor: str | None = None
