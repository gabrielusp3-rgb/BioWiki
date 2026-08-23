from __future__ import annotations

import uuid
from datetime import date, datetime

from app.models.enums import AssemblyLevel
from app.schemas.common import CamelModel


class GenomeRead(CamelModel):
    id: uuid.UUID
    accession: str
    assembly_name: str | None = None
    description: str | None = None
    organism: str
    tax_id: int
    source: str
    assembly_level: AssemblyLevel
    total_length: int | None = None
    chromosome_count: int | None = None
    scaffold_count: int | None = None
    contig_count: int | None = None
    gc_content: float | None = None
    release_date: date | None = None
    source_url: str | None = None
    updated_at: datetime | None = None
