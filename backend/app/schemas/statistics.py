from __future__ import annotations

from datetime import datetime

from app.schemas.common import CamelModel


class CategoryStat(CamelModel):
    key: str
    label: str
    count: int
    total_residues: int


class LastRun(CamelModel):
    source_key: str
    kind: str
    status: str
    finished_at: datetime | None = None
    created: int | None = None
    updated: int | None = None
    failed: int | None = None


class SyncInfo(CamelModel):
    status: str
    active_imports: int
    counts_in_sync: bool
    last_run: LastRun | None = None


class IntegrityCheck(CamelModel):
    name: str
    ok: bool
    detail: str
    expected: int | None = None
    actual: int | None = None


class IntegrityReport(CamelModel):
    ok: bool
    checked_at: datetime
    checks: list[IntegrityCheck]


class StatisticsRead(CamelModel):
    total_sequences: int
    total_residues: int
    organisms: int
    genes: int
    genomes: int
    publications: int
    linked_publications: int
    categories: list[CategoryStat]
    sync: SyncInfo
    last_updated: datetime | None = None
