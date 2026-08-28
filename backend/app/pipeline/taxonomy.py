"""NCBI Taxonomy payloads → lineage and OrganismGroup.

Division labels such as ``Plants and Fungi`` or ``Invertebrates`` are not a
safe kingdom mapping on their own. Lineage from the Taxonomy record is the
source of truth; division is only a last resort when lineage is absent.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

from app.pipeline.validation import infer_group_from_lineage

# NCBI ESummary/EFetch ``Division`` values that map unambiguously.
# ``Plants and Fungi`` is intentionally omitted — it is not a single kingdom.
_NCBI_DIVISION_TO_GROUP = {
    "bacteria": "bacteria",
    "plants": "plant",
    "fungi": "fungus",
    "viruses": "virus",
    "phages": "virus",
    "archaea": "archaea",
    "protozoa": "protozoan",
    "vertebrates": "animal",
    "mammals": "animal",
    "rodents": "animal",
    "primates": "animal",
}


def parse_ncbi_taxonomy_xml(xml: str) -> dict[int, dict[str, Any]]:
    """Parse an NCBI Taxonomy EFetch XML document.

    Only top-level ``Taxon`` elements are kept (LineageEx nested taxa are ignored).
    """
    root = ET.fromstring(xml)
    records: dict[int, dict[str, Any]] = {}
    for taxon in list(root):
        tag = taxon.tag.rsplit("}", 1)[-1]
        if tag != "Taxon":
            continue
        tax_text = taxon.findtext("TaxId")
        if not tax_text or not tax_text.isdigit():
            continue
        lineage_text = taxon.findtext("Lineage") or ""
        lineage = [
            part.strip()
            for part in lineage_text.split(";")
            if part.strip() and part.strip().lower() != "cellular organisms"
        ]
        records[int(tax_text)] = {
            "scientific_name": taxon.findtext("ScientificName"),
            "common_name": taxon.findtext("CommonName"),
            "division": taxon.findtext("Division"),
            "rank": taxon.findtext("Rank"),
            "lineage": lineage,
        }
    return records


def group_from_taxonomy(
    *,
    lineage: list[str] | None,
    division: str | None,
) -> str | None:
    """Classify OrganismGroup from official NCBI lineage, then division."""
    inferred = infer_group_from_lineage(lineage)
    if inferred:
        return inferred
    if not division:
        return None
    return _NCBI_DIVISION_TO_GROUP.get(division.strip().lower())
