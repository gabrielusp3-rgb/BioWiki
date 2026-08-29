"""Two different target semantics: additional sequences vs total publications.

The original +10,000 plan used approximate NEW-category shares. After DNA/RNA
overshoot those shares remain scientific reference goals, not delete-to-fit
quotas. The global sequence ceiling is soft: underfilled categories continue.
"""

from __future__ import annotations

# Approximate NEW records from the original +10,000 biodiversity plan.
CATEGORY_NEW_GOALS: dict[str, int] = {
    "dna": 2500,
    "rna": 2000,
    "protein": 3000,
    "virus": 1200,
    "crispr": 1000,
}

# Categories that may be frozen once their NEW goal is already exceeded.
FROZEN_WHEN_OVERFILLED: tuple[str, ...] = ("dna", "rna")

# Resume / future interleave order. Deficit-priority may reorder the first four.
PRIORITY_CATEGORIES: tuple[str, ...] = ("protein", "virus", "crispr", "genome")
INTERLEAVE_ORDER: tuple[str, ...] = (
    "protein",
    "virus",
    "crispr",
    "genome",
    "dna",
    "rna",
)


def sequence_ceiling(baseline_sequences: int, additional_sequences: int) -> int:
    """Final sequence count to stop at: baseline + requested new records."""
    if additional_sequences < 0:
        raise ValueError("additional_sequences must be >= 0")
    if baseline_sequences < 0:
        raise ValueError("baseline_sequences must be >= 0")
    return baseline_sequences + additional_sequences


def publication_remaining(current_publications: int, publication_target: int) -> int:
    """How many publication rows are still wanted. Target is TOTAL, not additional."""
    if publication_target < 0:
        raise ValueError("publication_target must be >= 0")
    return max(0, publication_target - max(0, current_publications))


def species_new_cap(additional_sequences: int, *, fraction: float = 0.03, floor: int = 8) -> int:
    """Soft anti-dominance cap on NEW records per species.

    This is a selection guardrail, not a biological law. Callers should skip
    further candidates from a species once the cap is reached and diversify,
    not delete already-validated records.
    """
    if additional_sequences <= 0:
        return floor
    return max(floor, int(additional_sequences * fraction))


def species_over_new_cap(
    tax_id: int,
    new_by_tax_id: dict[int, int],
    additional_sequences: int,
    *,
    fraction: float = 0.03,
) -> bool:
    cap = species_new_cap(additional_sequences, fraction=fraction)
    return int(new_by_tax_id.get(tax_id, 0)) >= cap


def category_new_count(category: str, new_by_category: dict[str, int] | None) -> int:
    return int((new_by_category or {}).get(category) or 0)


def category_deficit(category: str, new_by_category: dict[str, int] | None) -> int:
    """How many NEW records this category still wants. Never negative."""
    goal = CATEGORY_NEW_GOALS.get(category)
    if goal is None:
        return 0
    return max(0, goal - category_new_count(category, new_by_category))


def category_deficits(new_by_category: dict[str, int] | None) -> dict[str, int]:
    return {category: category_deficit(category, new_by_category) for category in CATEGORY_NEW_GOALS}
