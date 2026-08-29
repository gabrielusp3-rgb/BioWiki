"""Official NCBI Taxonomy name / TaxID classification. No invented names."""

from __future__ import annotations

from typing import Any

VALID_NAME = "VALID_NAME"
UPDATED_CANONICAL_NAME = "UPDATED_CANONICAL_NAME"
VALID_SYNONYM = "VALID_SYNONYM"
MERGED_TAXID = "MERGED_TAXID"
UNRESOLVED = "UNRESOLVED"


def normalize_scientific_name(name: str | None) -> str:
    return " ".join((name or "").strip().lower().split())


def classify_organism_taxonomy(
    *,
    stored_tax_id: int,
    stored_name: str,
    ncbi: dict[str, Any] | None,
) -> dict[str, Any]:
    """Compare a stored organism with one NCBI Taxonomy record.

    ``ncbi`` is the dict produced by ``parse_ncbi_taxonomy_xml`` (canonical
    ``tax_id``, ``scientific_name``, ``synonyms``, ``aka_tax_ids``, lineage).
    """
    if not ncbi:
        return {
            "status": UNRESOLVED,
            "canonical_tax_id": None,
            "canonical_name": None,
            "stored_name": stored_name,
            "stored_tax_id": stored_tax_id,
        }

    canonical_id = int(ncbi.get("tax_id") or stored_tax_id)
    canonical_name = (ncbi.get("scientific_name") or "").strip() or None
    synonyms = [str(s) for s in (ncbi.get("synonyms") or []) if str(s).strip()]
    stored_n = normalize_scientific_name(stored_name)
    canonical_n = normalize_scientific_name(canonical_name)
    synonym_n = {normalize_scientific_name(s) for s in synonyms}

    merged = canonical_id != int(stored_tax_id)
    if merged:
        status = MERGED_TAXID
    elif stored_n and stored_n == canonical_n:
        status = VALID_NAME
    elif stored_n and stored_n in synonym_n:
        status = VALID_SYNONYM
    elif stored_n and canonical_n and stored_n != canonical_n:
        status = UPDATED_CANONICAL_NAME
    elif not stored_n:
        status = UNRESOLVED
    else:
        status = VALID_NAME

    return {
        "status": status,
        "canonical_tax_id": canonical_id,
        "canonical_name": canonical_name,
        "stored_name": stored_name,
        "stored_tax_id": stored_tax_id,
        "synonyms": synonyms,
        "rank": ncbi.get("rank"),
        "lineage": list(ncbi.get("lineage") or []),
        "division": ncbi.get("division"),
    }
