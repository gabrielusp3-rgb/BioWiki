"""Import worker: orchestrates parse → validate → persist.

- Per-record SAVEPOINTs isolate failures so one bad record never aborts a batch.
- Batched commits keep memory/transaction sizes bounded for large imports.
- Every skip/failure is logged with a reason and surfaced in the ImportReport.

Nothing here downloads data or invents content; callers provide the source text
(from a file or a connector) and the classification context.
"""

from __future__ import annotations

import os
from collections.abc import Iterable
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.database.session import get_sessionmaker
from app.pipeline import validation
from app.pipeline.errors import ValidationError
from app.pipeline.logging import get_logger
from app.pipeline.models import ImportContext, ImportReport, ParsedSequence
from app.pipeline.parsers.registry import get_parser

logger = get_logger("biowiki.pipeline.import")

_EXT_TO_FORMAT = {
    ".fasta": "fasta", ".fa": "fasta", ".fna": "fasta", ".faa": "fasta",
    ".gb": "genbank", ".gbk": "genbank", ".genbank": "genbank",
    ".json": "json",
    ".csv": "csv",
}


class ImportWorker:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
        *,
        batch_size: int = 200,
    ) -> None:
        self.session_factory = session_factory or get_sessionmaker()
        self.batch_size = max(1, batch_size)

    async def run(self, parsed: Iterable[ParsedSequence]) -> ImportReport:
        from app.pipeline.importers.sequence_importer import SequenceImporter

        report = ImportReport()
        pending = 0

        async with self.session_factory() as session:
            importer = SequenceImporter(session)
            for ps in parsed:
                report.total += 1

                try:
                    validation.enrich(ps)
                    validation.validate(ps)
                except ValidationError as exc:
                    report.skipped += 1
                    msg = f"skip {ps.accession or '<no-accession>'}: {exc}"
                    report.errors.append(msg)
                    logger.warning(msg)
                    continue
                except Exception as exc:  # noqa: BLE001 — never abort a batch on one record
                    report.skipped += 1
                    msg = f"skip {ps.accession or '<no-accession>'}: {exc}"
                    report.errors.append(msg)
                    logger.exception(msg)
                    continue

                try:
                    async with session.begin_nested():
                        _, created = await importer.upsert_sequence(ps)
                    if created:
                        report.created += 1
                    else:
                        report.updated += 1
                    pending += 1
                    if pending >= self.batch_size:
                        await session.commit()
                        logger.info(
                            "committed batch: created=%d updated=%d skipped=%d failed=%d",
                            report.created, report.updated, report.skipped, report.failed,
                        )
                        pending = 0
                except Exception as exc:  # noqa: BLE001 — isolate per-record failures
                    report.failed += 1
                    msg = f"fail {ps.accession or '<no-accession>'}: {exc}"
                    report.errors.append(msg)
                    logger.exception(msg)

            await session.commit()

        logger.info("import finished: %s", report.as_dict())
        return report


async def import_records(
    records: Iterable[ParsedSequence],
    *,
    session_factory: async_sessionmaker[AsyncSession] | None = None,
    batch_size: int = 200,
) -> ImportReport:
    worker = ImportWorker(session_factory, batch_size=batch_size)
    return await worker.run(records)


async def import_text(
    text: str,
    fmt: str,
    context: ImportContext,
    *,
    session_factory: async_sessionmaker[AsyncSession] | None = None,
    batch_size: int = 200,
) -> ImportReport:
    parser = get_parser(fmt)
    logger.info("parsing input as %s for source=%s", parser.fmt, context.source_key)
    return await import_records(
        parser.parse(text, context),
        session_factory=session_factory,
        batch_size=batch_size,
    )


async def import_file(
    path: str | os.PathLike[str],
    context: ImportContext,
    *,
    fmt: str | None = None,
    session_factory: async_sessionmaker[AsyncSession] | None = None,
    batch_size: int = 200,
    encoding: str = "utf-8",
) -> ImportReport:
    file_path = Path(path)
    resolved_fmt = fmt or _EXT_TO_FORMAT.get(file_path.suffix.lower())
    if resolved_fmt is None:
        raise ValueError(f"Cannot infer format from {file_path.suffix!r}; pass fmt explicitly.")
    text = file_path.read_text(encoding=encoding)
    logger.info("importing file %s (%s)", file_path, resolved_fmt)
    return await import_text(
        text, resolved_fmt, context,
        session_factory=session_factory, batch_size=batch_size,
    )
