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


def _local_tag(element: ET.Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def _collect_synonyms(taxon: ET.Element) -> list[str]:
    names: list[str] = []
    other = taxon.find("OtherNames")
    if other is None:
        return names
    for child in other:
        tag = _local_tag(child)
        if tag in {"Synonym", "EquivalentName", "GenbankSynonym", "Anamorph", "GenbankAnamorph"}:
            text = (child.text or "").strip()
            if text:
                names.append(text)
        elif tag == "Name":
            class_cde = child.findtext("ClassCDE") or ""
            disp = (child.findtext("DispName") or child.text or "").strip()
            if disp and class_cde.lower() in {"synonym", "equivalent name", "genbank synonym"}:
                names.append(disp)
    return names


def _collect_aka_tax_ids(taxon: ET.Element) -> list[int]:
    ids: list[int] = []
    aka = taxon.find("AkaTaxIds")
    if aka is None:
        return ids
    for child in aka:
        if _local_tag(child) != "TaxId":
            continue
        text = (child.text or "").strip()
        if text.isdigit():
            ids.append(int(text))
    return ids


def parse_ncbi_taxonomy_xml(xml: str) -> dict[int, dict[str, Any]]:
    """Parse an NCBI Taxonomy EFetch XML document.

    Only top-level ``Taxon`` elements are kept (LineageEx nested taxa are ignored).
    Merged identifiers listed in ``AkaTaxIds`` index the same canonical record
    so a caller asking for an old TaxID still retrieves the current taxon.
    """
    root = ET.fromstring(xml)
    records: dict[int, dict[str, Any]] = {}
    for taxon in list(root):
        if _local_tag(taxon) != "Taxon":
            continue
        tax_text = taxon.findtext("TaxId")
        if not tax_text or not tax_text.isdigit():
            continue
        canonical_id = int(tax_text)
        lineage_text = taxon.findtext("Lineage") or ""
        lineage = [
            part.strip()
            for part in lineage_text.split(";")
            if part.strip() and part.strip().lower() != "cellular organisms"
        ]
        record = {
            "tax_id": canonical_id,
            "scientific_name": taxon.findtext("ScientificName"),
            "common_name": taxon.findtext("CommonName"),
            "division": taxon.findtext("Division"),
            "rank": taxon.findtext("Rank"),
            "lineage": lineage,
            "synonyms": _collect_synonyms(taxon),
            "aka_tax_ids": _collect_aka_tax_ids(taxon),
        }
        records[canonical_id] = record
        for aka in record["aka_tax_ids"]:
            records.setdefault(aka, record)
    return records


def index_taxonomy_for_requested(
    xml: str, requested_tax_ids: list[int]
) -> dict[int, dict[str, Any]]:
    """Map each requested TaxID onto the NCBI record, including merged IDs.

    When NCBI returns only the canonical taxon for a merged request and omits
    ``AkaTaxIds``, a single-id response is still bound to that request.
    """
    parsed = parse_ncbi_taxonomy_xml(xml)
    out: dict[int, dict[str, Any]] = {}
    unique_requested = list(dict.fromkeys(requested_tax_ids))
    for tax_id in unique_requested:
        if tax_id in parsed:
            out[tax_id] = parsed[tax_id]
    missing = [tax_id for tax_id in unique_requested if tax_id not in out]
    unique_canonical = {
        rec["tax_id"]: rec for rec in parsed.values() if rec.get("tax_id") is not None
    }
    if len(missing) == 1 and len(unique_canonical) == 1:
        out[missing[0]] = next(iter(unique_canonical.values()))
    return out


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
