"""Category-aware expansion scheduling.

DNA/RNA must not consume a global sequence ceiling before Protein, Virus,
CRISPR and Genome jobs get their reserved scientific opportunity. The global
count is a soft reference, not a hard stop for underfilled categories.
"""

from __future__ import annotations

from collections import deque
from typing import Any

from app.pipeline.expansion.targets import (
    CATEGORY_NEW_GOALS,
    FROZEN_WHEN_OVERFILLED,
    INTERLEAVE_ORDER,
    PRIORITY_CATEGORIES,
    category_deficit,
    category_deficits,
)

DEFERRED_CATEGORY_OVERFILLED = "DEFERRED_CATEGORY_OVERFILLED"


def frozen_categories(new_by_category: dict[str, int] | None) -> set[str]:
    """Categories that already met their NEW-record goal and must wait."""
    frozen: set[str] = set()
    counts = new_by_category or {}
    for category in FROZEN_WHEN_OVERFILLED:
        if category_deficit(category, counts) <= 0 and int(counts.get(category) or 0) > 0:
            frozen.add(category)
    return frozen


def skip_status(
    job: dict[str, Any],
    *,
    new_by_category: dict[str, int] | None,
    stats: dict[str, Any] | None = None,
    additional: int = 0,
    ceiling: int = 0,
) -> str | None:
    """Return a checkpoint status if this job must not run now.

    Protein, virus, CRISPR, genome, and the computational NGG job are never
    stopped by a global sequence ceiling. Overfilled DNA/RNA are deferred,
    not marked completed.
    """
    del stats, additional, ceiling  # global ceiling is intentionally unused
    if job.get("kind") == "computational_ngg":
        return None
    category = str(job.get("category") or "")
    if category in frozen_categories(new_by_category):
        return DEFERRED_CATEGORY_OVERFILLED
    return None


def interleave_order(new_by_category: dict[str, int] | None) -> list[str]:
    """Deficit-priority order, then the stable interleave list."""
    deficits = category_deficits(new_by_category)
    priority = sorted(
        PRIORITY_CATEGORIES,
        key=lambda cat: (-int(deficits.get(cat) or 0), INTERLEAVE_ORDER.index(cat)),
    )
    rest = [cat for cat in INTERLEAVE_ORDER if cat not in priority]
    return priority + rest


def schedule_jobs(
    jobs: list[dict[str, Any]],
    *,
    new_by_category: dict[str, int] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Split jobs into an interleaved runnable queue and deferred jobs.

    Deferred jobs keep their plan identity so they can be reconsidered later.
    They are not treated as completed.
    """
    frozen = frozen_categories(new_by_category)
    deferred: list[dict[str, Any]] = []
    queues: dict[str, deque[dict[str, Any]]] = {}
    for job in jobs:
        category = str(job.get("category") or "other")
        if job.get("kind") != "computational_ngg" and category in frozen:
            deferred.append(job)
            continue
        queues.setdefault(category, deque()).append(job)

    order = [cat for cat in interleave_order(new_by_category) if queues.get(cat)]
    for category in list(queues):
        if category not in order:
            order.append(category)

    scheduled: list[dict[str, Any]] = []
    while any(queues.get(cat) for cat in order):
        progressed = False
        for category in order:
            bucket = queues.get(category)
            if bucket:
                scheduled.append(bucket.popleft())
                progressed = True
        if not progressed:
            break
    return scheduled, deferred


def deficient_categories(new_by_category: dict[str, int] | None) -> set[str]:
    """Categories that still need discovery (never DNA/RNA once overfilled)."""
    frozen = frozen_categories(new_by_category)
    out: set[str] = set()
    for category in CATEGORY_NEW_GOALS:
        if category in frozen:
            continue
        if category_deficit(category, new_by_category) > 0:
            out.add(category)
    return out
