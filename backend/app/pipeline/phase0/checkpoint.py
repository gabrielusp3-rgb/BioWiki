"""JSON checkpoint for the Phase 0 scientific audit.

Network failures are stored as TEMPORARILY_UNVERIFIED and retried on resume.
Verified / superseded / invalid classifications are not repeated.
The file is written atomically (temp + replace) so an interrupt cannot
leave a truncated checkpoint.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TERMINAL_STATUSES = frozenset(
    {"VERIFIED", "SUPERSEDED", "MISMATCH", "INVALID"}
)
RETRYABLE_STATUSES = frozenset({"TEMPORARILY_UNVERIFIED", "PENDING"})

CHECKPOINT_VERSION = 1


def default_checkpoint() -> dict[str, Any]:
    return {
        "version": CHECKPOINT_VERSION,
        "updated_at": None,
        "last_completed_position": None,
        "processed": 0,
        "verified": 0,
        "temporary_failures": 0,
        "mismatches": 0,
        "invalid": 0,
        "superseded": 0,
        "records": {},
        "organisms": {},
        "publications": {},
        "genomes": {},
    }


def load_checkpoint(path: Path) -> dict[str, Any]:
    if not path.exists():
        return default_checkpoint()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default_checkpoint()
    if not isinstance(payload, dict) or payload.get("version") != CHECKPOINT_VERSION:
        base = default_checkpoint()
        if isinstance(payload, dict):
            for key in ("records", "organisms", "publications", "genomes"):
                if isinstance(payload.get(key), dict):
                    base[key] = payload[key]
        return base
    merged = default_checkpoint()
    merged.update(payload)
    for key in ("records", "organisms", "publications", "genomes"):
        if not isinstance(merged.get(key), dict):
            merged[key] = {}
    return merged


def save_checkpoint(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data["version"] = CHECKPOINT_VERSION
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    _recount(data)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    tmp.replace(path)


def record_key(source: str, accession: str, version: str | None) -> str:
    return f"{source}|{accession}|{version or ''}"


def needs_retry(entry: dict[str, Any] | None) -> bool:
    if not entry:
        return True
    status = str(entry.get("status") or "PENDING")
    return status in RETRYABLE_STATUSES or status not in TERMINAL_STATUSES | RETRYABLE_STATUSES


def mark(
    bucket: dict[str, Any],
    key: str,
    *,
    status: str,
    **fields: Any,
) -> dict[str, Any]:
    row = {"status": status, **fields}
    bucket[key] = row
    return row


def _recount(data: dict[str, Any]) -> None:
    statuses: dict[str, int] = {}
    processed = 0
    for bucket_name in ("records", "organisms", "publications", "genomes"):
        for entry in (data.get(bucket_name) or {}).values():
            if not isinstance(entry, dict):
                continue
            processed += 1
            status = str(entry.get("status") or "PENDING")
            statuses[status] = statuses.get(status, 0) + 1
    data["processed"] = processed
    data["verified"] = statuses.get("VERIFIED", 0)
    data["temporary_failures"] = statuses.get("TEMPORARILY_UNVERIFIED", 0)
    data["mismatches"] = statuses.get("MISMATCH", 0)
    data["invalid"] = statuses.get("INVALID", 0)
    data["superseded"] = statuses.get("SUPERSEDED", 0)
    data["by_status"] = statuses
