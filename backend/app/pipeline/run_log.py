"""Persistent import logging: records every pipeline execution in the database.

Usage::

    async with record_run("ncbi_genbank", "fetch_accessions", params) as run:
        report = await import_records(...)
        run.set_report(report)

The run row is committed immediately with status ``running`` and finalised as
``succeeded`` or ``failed`` — even when the body raises — so partial imports
remain auditable.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.database.session import get_sessionmaker
from app.models.ingestion import IngestionRun
from app.pipeline.logging import get_logger
from app.pipeline.models import ImportReport

logger = get_logger("biowiki.pipeline.runs")

_MAX_LOGGED_ERRORS = 50


class RunHandle:
    """Mutable handle the caller uses to attach the final report to a run."""

    def __init__(self, run_id) -> None:
        self.run_id = run_id
        self.report: ImportReport | None = None

    def set_report(self, report: ImportReport) -> None:
        self.report = report


@asynccontextmanager
async def record_run(
    source_key: str,
    kind: str,
    params: dict | None = None,
    *,
    session_factory: async_sessionmaker[AsyncSession] | None = None,
):
    factory = session_factory or get_sessionmaker()

    async with factory() as session:
        run = IngestionRun(source_key=source_key, kind=kind, params=params, status="running")
        session.add(run)
        await session.commit()
        run_id = run.id
    logger.info("ingestion run %s started: %s/%s %s", run_id, source_key, kind, params)

    handle = RunHandle(run_id)
    status = "succeeded"
    try:
        yield handle
    except Exception:
        status = "failed"
        raise
    finally:
        async with factory() as session:
            run = await session.get(IngestionRun, run_id)
            if run is not None:
                run.status = status
                run.finished_at = datetime.now(timezone.utc)
                if handle.report is not None:
                    report = handle.report
                    run.total = report.total
                    run.created = report.created
                    run.updated = report.updated
                    run.skipped = report.skipped
                    run.failed = report.failed
                    run.errors = report.errors[:_MAX_LOGGED_ERRORS] or None
                    if report.failed and status == "succeeded":
                        # Partial failures are surfaced, not hidden.
                        run.status = "succeeded" if report.created or report.updated else "failed"
                await session.commit()
        logger.info("ingestion run %s finished: %s", run_id, status)
