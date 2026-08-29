"""Resumable expansion checkpoint. No secrets. Written under backend/data/."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CHECKPOINT_VERSION = 3
DEFAULT_CHECKPOINT_PATH = (
    Path(__file__).resolve().parents[3] / "data" / "expansion_checkpoint.json"
)

PENDING = "PENDING"
RUNNING = "RUNNING"
COMPLETED_SUCCESSFULLY = "COMPLETED_SUCCESSFULLY"
SKIPPED_ALREADY_PRESENT = "SKIPPED_ALREADY_PRESENT"
DEFERRED_CATEGORY_OVERFILLED = "DEFERRED_CATEGORY_OVERFILLED"
TEMPORARY_FAILURE = "TEMPORARY_FAILURE"
FAILED = "FAILED"

RERUN_BLOCKING = {COMPLETED_SUCCESSFULLY, SKIPPED_ALREADY_PRESENT}


def default_checkpoint() -> dict[str, Any]:
    return {
        "version": CHECKPOINT_VERSION,
        "job_id": None,
        "source": None,
        "category": None,
        "candidate_position": None,
        "accession": None,
        "batch_number": 0,
        "processed": 0,
        "verified": 0,
        "inserted": 0,
        "updated": 0,
        "skipped": 0,
        "temporary_failure": 0,
        "permanent_failure": 0,
        "completed": [],
        "failed": {},
        "failed_history": {},
        "job_status": {},
        "reports": [],
        "new_by_tax_id": {},
        "config": {},
        "before": None,
        "after": None,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": None,
        "notes": {},
    }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def set_job_status(
    checkpoint: dict[str, Any],
    job_id: str,
    status: str,
    *,
    category: str | None = None,
    source: str | None = None,
    records_created: int = 0,
    records_updated: int = 0,
    records_skipped: int = 0,
    reason: str | None = None,
    started_at: str | None = None,
    finished_at: str | None = None,
) -> dict[str, Any]:
    bucket = checkpoint.setdefault("job_status", {})
    entry = dict(bucket.get(job_id) or {})
    current = entry.get("status")
    if status == DEFERRED_CATEGORY_OVERFILLED and current in RERUN_BLOCKING:
        return entry
    if started_at or status == RUNNING:
        entry["started_at"] = started_at or entry.get("started_at") or _now()
    if status != RUNNING:
        entry["finished_at"] = finished_at or _now()
    entry.update(
        {
            "status": status,
            "category": category if category is not None else entry.get("category"),
            "source": source if source is not None else entry.get("source"),
            "records_created": int(records_created),
            "records_updated": int(records_updated),
            "records_skipped": int(records_skipped),
        }
    )
    if reason:
        entry["reason"] = reason
    bucket[job_id] = entry
    completed = set(checkpoint.get("completed") or [])
    if status in RERUN_BLOCKING:
        completed.add(job_id)
    elif status == DEFERRED_CATEGORY_OVERFILLED:
        completed.discard(job_id)
    checkpoint["completed"] = sorted(completed)
    return entry


def job_is_done(checkpoint: dict[str, Any], job_id: str) -> bool:
    status = ((checkpoint.get("job_status") or {}).get(job_id) or {}).get("status")
    if status in RERUN_BLOCKING:
        return True
    return job_id in set(checkpoint.get("completed") or []) and status != DEFERRED_CATEGORY_OVERFILLED


def migrate_checkpoint(data: dict[str, Any]) -> dict[str, Any]:
    """Upgrade v2 completed[]/reports into explicit job_status entries."""
    reports = {
        str(row.get("id")): row
        for row in (data.get("reports") or [])
        if isinstance(row, dict) and row.get("id")
    }
    job_status = dict(data.get("job_status") or {})
    kept_completed: list[str] = []
    for job_id in data.get("completed") or []:
        job_id = str(job_id)
        report = reports.get(job_id)
        if report is not None:
            job_status[job_id] = {
                "status": COMPLETED_SUCCESSFULLY,
                "records_created": int(report.get("created") or 0),
                "records_updated": int(report.get("updated") or 0),
                "records_skipped": int(report.get("skipped") or 0),
                "reason": None,
            }
            kept_completed.append(job_id)
            continue
        existing = job_status.get(job_id) or {}
        if existing.get("status") in RERUN_BLOCKING:
            kept_completed.append(job_id)
            continue
        if job_id.startswith("pubmed-") or job_id.startswith("pm-"):
            job_status[job_id] = {
                "status": COMPLETED_SUCCESSFULLY,
                "reason": "legacy pubmed checkpoint without ingest report",
            }
            kept_completed.append(job_id)
            continue
        job_status[job_id] = {
            "status": DEFERRED_CATEGORY_OVERFILLED,
            "reason": "legacy completed[] without ingest report; not treated as completed",
        }
    data["job_status"] = job_status
    data["completed"] = sorted(set(kept_completed))
    data["version"] = CHECKPOINT_VERSION
    return data


def apply_succeeded_runs(
    checkpoint: dict[str, Any],
    runs: list[dict[str, Any]],
    *,
    job_categories: dict[str, str] | None = None,
) -> list[str]:
    """Mark jobs whose DB ingest succeeded but the checkpoint write was lost.

    Does not invent counts. ``runs`` must come from real IngestionRun rows.
    """
    categories = job_categories or {}
    reports = {str(row.get("id")) for row in (checkpoint.get("reports") or []) if row.get("id")}
    reconciled: list[str] = []
    for run in runs:
        if str(run.get("status") or "") != "succeeded":
            continue
        job_id = str(run.get("job_id") or "").strip()
        if not job_id:
            continue
        current = ((checkpoint.get("job_status") or {}).get(job_id) or {}).get("status")
        if current == COMPLETED_SUCCESSFULLY or job_id in reports:
            if job_id not in set(checkpoint.get("completed") or []):
                set_job_status(
                    checkpoint,
                    job_id,
                    COMPLETED_SUCCESSFULLY,
                    category=categories.get(job_id),
                    records_created=int(run.get("created") or 0),
                    records_updated=int(run.get("updated") or 0),
                    records_skipped=int(run.get("skipped") or 0),
                    finished_at=run.get("finished_at"),
                    reason="reconciled from ingestion_runs",
                )
                reconciled.append(job_id)
            continue
        created = int(run.get("created") or 0)
        updated = int(run.get("updated") or 0)
        skipped = int(run.get("skipped") or 0)
        set_job_status(
            checkpoint,
            job_id,
            COMPLETED_SUCCESSFULLY,
            category=categories.get(job_id),
            source="ingestion_run",
            records_created=created,
            records_updated=updated,
            records_skipped=skipped,
            finished_at=run.get("finished_at"),
            reason="commit-before-checkpoint reconcile",
        )
        checkpoint["inserted"] = int(checkpoint.get("inserted") or 0) + created
        checkpoint["updated"] = int(checkpoint.get("updated") or 0) + updated
        category = categories.get(job_id)
        if category and created:
            bucket = checkpoint.setdefault("new_by_category", {})
            bucket[category] = int(bucket.get(category) or 0) + created
        checkpoint.setdefault("reports", []).append(
            {
                "id": job_id,
                "total": int(run.get("total") or created + updated + skipped),
                "created": created,
                "updated": updated,
                "skipped": skipped,
                "failed": 0,
                "errors": [],
                "reconciled": True,
            }
        )
        reconciled.append(job_id)
    return reconciled


def load_checkpoint(path: Path) -> dict[str, Any]:
    if not path.exists():
        return default_checkpoint()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default_checkpoint()
    if not isinstance(payload, dict):
        return default_checkpoint()
    merged = default_checkpoint()
    merged.update(payload)
    if not isinstance(merged.get("completed"), list):
        merged["completed"] = []
    if not isinstance(merged.get("failed"), dict):
        merged["failed"] = {}
    if not isinstance(merged.get("new_by_tax_id"), dict):
        merged["new_by_tax_id"] = {}
    if not isinstance(merged.get("job_status"), dict):
        merged["job_status"] = {}
    return migrate_checkpoint(merged)


def save_checkpoint(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data["version"] = CHECKPOINT_VERSION
    data["updated_at"] = _now()
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    tmp.replace(path)


def tax_counts(checkpoint: dict[str, Any]) -> dict[int, int]:
    raw = checkpoint.get("new_by_tax_id") or {}
    out: dict[int, int] = {}
    for key, value in raw.items():
        try:
            out[int(key)] = int(value)
        except (TypeError, ValueError):
            continue
    return out


def add_new_tax(checkpoint: dict[str, Any], tax_id: int, n: int = 1) -> None:
    if n <= 0 or tax_id <= 0:
        return
    counts = checkpoint.setdefault("new_by_tax_id", {})
    key = str(tax_id)
    counts[key] = int(counts.get(key) or 0) + n
