"""Two different target semantics: additional sequences vs total publications."""

from __future__ import annotations


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
