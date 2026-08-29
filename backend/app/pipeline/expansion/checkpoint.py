"""Resumable expansion checkpoint. No secrets. Written under backend/data/."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CHECKPOINT_VERSION = 2
DEFAULT_CHECKPOINT_PATH = (
    Path(__file__).resolve().parents[3] / "data" / "expansion_checkpoint.json"
)


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
        "reports": [],
        "new_by_tax_id": {},
        "config": {},
        "before": None,
        "after": None,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": None,
        "notes": {},
    }


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
    return merged


def save_checkpoint(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data["version"] = CHECKPOINT_VERSION
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
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
