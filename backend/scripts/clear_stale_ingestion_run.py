"""Operator cleanup: close a stale ingestion_runs row stuck in status=running.

Read-only unless --apply. Does not touch catalogue tables.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_sessionmaker
from app.models.ingestion import IngestionRun


async def _inspect(session: AsyncSession) -> list[dict]:
    rows = list(
        (
            await session.execute(
                select(IngestionRun).where(IngestionRun.status == "running").order_by(
                    IngestionRun.started_at
                )
            )
        ).scalars()
    )
    payload = []
    for row in rows:
        payload.append(
            {
                "id": str(row.id),
                "source_key": row.source_key,
                "kind": row.kind,
                "status": row.status,
                "started_at": row.started_at.isoformat() if row.started_at else None,
                "finished_at": row.finished_at.isoformat() if row.finished_at else None,
                "created": row.created,
                "updated": row.updated,
                "failed": row.failed,
            }
        )
    return payload


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    async with get_sessionmaker()() as session:
        running = await _inspect(session)
        print(json.dumps({"running": running, "apply": args.apply}, indent=2))
        if not running:
            print("no running ingestion rows")
            return 0
        if not args.apply:
            print("dry-run: pass --apply to mark stale running rows failed")
            return 0
        now = datetime.now(timezone.utc)
        ids = [row["id"] for row in running]
        for item in running:
            run = await session.get(IngestionRun, item["id"])
            if run is None:
                continue
            run.status = "failed"
            # Keep finished_at on the interruption day so a later successful
            # import remains lastRun for /statistics.sync.
            started = run.started_at
            run.finished_at = (started + timedelta(minutes=1)) if started else now
            run.errors = {
                "reason": "operator_closeout_stale_running",
                "detail": (
                    "No live CLI ingest was running; the row remained "
                    "status=running after process interruption."
                ),
                "closed_at": now.isoformat(),
            }
        await session.commit()
        print(json.dumps({"updated": ids, "new_status": "failed"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
