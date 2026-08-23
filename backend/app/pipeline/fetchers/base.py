"""Shared fetcher helpers: batch chunking and run-logged imports."""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from app.pipeline.models import ImportReport, ParsedSequence
from app.pipeline.run_log import record_run
from app.pipeline.workers.import_worker import import_records


def chunked(items: Sequence, size: int) -> Iterable[Sequence]:
    for start in range(0, len(items), size):
        yield items[start : start + size]


async def import_with_run(
    records: Iterable[ParsedSequence],
    *,
    source_key: str,
    kind: str,
    params: dict | None = None,
    batch_size: int = 200,
) -> ImportReport:
    """Run a validated batch import wrapped in an ``ingestion_runs`` entry."""
    async with record_run(source_key, kind, params) as run:
        report = await import_records(records, batch_size=batch_size)
        run.set_report(report)
    # Keep cached UI counters aligned with the rows we just wrote.
    if report.created or report.updated:
        from app.services.sync_service import refresh_counts_safely

        await refresh_counts_safely()
    return report
