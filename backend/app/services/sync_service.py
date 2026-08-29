"""Real-count synchronisation, sync-status and integrity checks.

Everything here reads live aggregates from the database. Numbers shown in the
UI must always be reconciled against these values — never estimates.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.models.enums import SequenceType
from app.models.genome import GenomeRecord
from app.models.ingestion import IngestionRun
from app.models.organism import Organism
from app.models.publication import Publication, SequenceReference
from app.models.sequence import Sequence
from app.schemas.statistics import IntegrityCheck, IntegrityReport, LastRun, SyncInfo

# Which sequence types roll up into each UI category.
CATEGORY_TYPES: dict[str, list[SequenceType]] = {
    "dna": [SequenceType.DNA],
    "rna": [SequenceType.RNA],
    "protein": [SequenceType.PROTEIN, SequenceType.PEPTIDE],
    "crispr": [SequenceType.CRISPR],
    "virus": [SequenceType.VIRUS],
    "genome": [SequenceType.GENOME],
}

CATEGORY_LABELS: dict[str, str] = {
    "dna": "DNA",
    "rna": "RNA",
    "protein": "Protein",
    "crispr": "CRISPR",
    "virus": "Virus",
    "genome": "Genome",
}


async def _category_live_counts(session: AsyncSession) -> dict[str, int]:
    """One GROUP BY plus genome_records count — same numbers as per-key COUNTs."""
    type_counts = {
        row[0]: int(row[1])
        for row in (
            await session.execute(
                select(Sequence.seq_type, func.count()).group_by(Sequence.seq_type)
            )
        ).all()
    }
    genome_rec = int(
        (await session.execute(select(func.count()).select_from(GenomeRecord))).scalar_one()
    )
    live: dict[str, int] = {}
    for key, types in CATEGORY_TYPES.items():
        if key == "genome":
            # Assemblies live in genome_records. SequenceType.GENOME rows are a
            # different entity and must not inflate the genome catalogue count.
            live[key] = genome_rec
        else:
            live[key] = sum(type_counts.get(seq_type, 0) for seq_type in types)
    return live


async def _live_category_count(session: AsyncSession, key: str) -> int:
    live = await _category_live_counts(session)
    return live.get(key, 0)


async def refresh_counts(session: AsyncSession) -> dict[str, int]:
    """Reconcile cached UI counters with live row counts (idempotent)."""
    updated: dict[str, int] = {}

    live = await _category_live_counts(session)
    existing = {
        cat.key: cat
        for cat in (await session.execute(select(Category))).scalars().all()
    }
    for key, label in CATEGORY_LABELS.items():
        cat = existing.get(key)
        if cat is None:
            cat = Category(key=key, label=label)
            session.add(cat)
        count = live.get(key, 0)
        cat.sequence_count = count
        updated[key] = count

    org_counts = dict(
        (
            await session.execute(
                select(Sequence.organism_id, func.count())
                .group_by(Sequence.organism_id)
            )
        ).all()
    )
    for org in (await session.execute(select(Organism))).scalars().all():
        org.sequence_count = int(org_counts.get(org.id, 0))

    await session.commit()
    return updated


async def refresh_counts_safely(session: AsyncSession | None = None) -> None:
    """Refresh cached counters without aborting an import.

    Fetchers call this after committing their own session; in that case a
    fresh session is opened. When a session is supplied, failures roll it back
    so the caller can continue.
    """
    if session is None:
        from app.database.session import get_sessionmaker

        async with get_sessionmaker()() as owned:
            try:
                await refresh_counts(owned)
            except Exception:  # pragma: no cover - never break an import over counters
                await owned.rollback()
        return
    try:
        await refresh_counts(session)
    except Exception:  # pragma: no cover - never break an import over counters
        await session.rollback()


async def _counts_in_sync(
    session: AsyncSession, live: dict[str, int] | None = None
) -> bool:
    if live is None:
        live = await _category_live_counts(session)
    for cat in (await session.execute(select(Category))).scalars().all():
        expected = live.get(cat.key, 0)
        if cat.sequence_count is None or int(cat.sequence_count) != expected:
            return False
    return True


async def _last_finished_run(session: AsyncSession) -> IngestionRun | None:
    stmt = (
        select(IngestionRun)
        .where(IngestionRun.status.in_(["succeeded", "failed"]))
        .order_by(IngestionRun.finished_at.desc().nullslast())
        .limit(1)
    )
    return (await session.execute(stmt)).scalars().first()


async def get_sync_status(
    session: AsyncSession,
    *,
    total_sequences: int | None = None,
    category_live: dict[str, int] | None = None,
) -> SyncInfo:
    total = (
        total_sequences
        if total_sequences is not None
        else int(
            (await session.execute(select(func.count()).select_from(Sequence))).scalar_one()
        )
    )
    active = int(
        (
            await session.execute(
                select(func.count()).where(IngestionRun.status == "running")
            )
        ).scalar_one()
    )
    last = await _last_finished_run(session)
    last_run = None
    if last is not None:
        last_run = LastRun(
            source_key=last.source_key,
            kind=last.kind,
            status=last.status,
            finished_at=last.finished_at,
            created=last.created,
            updated=last.updated,
            failed=last.failed,
        )

    in_sync = (
        await _counts_in_sync(session, live=category_live) if total > 0 else False
    )

    if total == 0:
        status = "empty"
    elif active > 0:
        status = "importing"
    elif last is not None and last.status == "failed":
        status = "error"
    elif in_sync:
        status = "updated"
    else:
        status = "connected"

    return SyncInfo(
        status=status,
        active_imports=active,
        counts_in_sync=in_sync,
        last_run=last_run,
    )


async def check_integrity(session: AsyncSession) -> IntegrityReport:
    from app.services.integrity_checks import sql_integrity_checks

    checks: list[IntegrityCheck] = []

    live = await _category_live_counts(session)
    for cat in (await session.execute(select(Category))).scalars().all():
        expected = live.get(cat.key, 0)
        cached = int(cat.sequence_count) if cat.sequence_count is not None else None
        ok = cached == expected
        checks.append(
            IntegrityCheck(
                name=f"category:{cat.key}",
                ok=ok,
                detail=(
                    "cached count matches live count"
                    if ok
                    else "cached count is stale — run a sync"
                ),
                expected=expected,
                actual=cached,
            )
        )

    checks.extend(await sql_integrity_checks(session))

    return IntegrityReport(
        ok=all(c.ok for c in checks),
        checked_at=datetime.now(timezone.utc),
        checks=checks,
    )
