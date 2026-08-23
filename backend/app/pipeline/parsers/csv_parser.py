"""CSV parser.

Expects a header row. Recognised columns map onto :class:`ParsedSequence`
fields; ``pdb_ids`` and ``domains`` accept ``;``-separated values. Unknown
columns are ignored; missing provenance falls back to the import context.
"""

from __future__ import annotations

import csv
import io
from collections.abc import Iterator
from typing import Any

from app.pipeline.models import ImportContext, ParsedOrganism, ParsedSequence
from app.pipeline.parsers.base import BaseParser


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


def _to_int(value: str | None) -> int | None:
    value = _clean(value)
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _to_float(value: str | None) -> float | None:
    value = _clean(value)
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _to_bool(value: str | None) -> bool | None:
    value = _clean(value)
    if value is None:
        return None
    return value.lower() in {"1", "true", "yes", "y", "reviewed"}


def _to_list(value: str | None) -> list[str]:
    value = _clean(value)
    if not value:
        return []
    return [v.strip() for v in value.split(";") if v.strip()]


class CsvParser(BaseParser):
    fmt = "csv"

    def parse(self, text: str, context: ImportContext) -> Iterator[ParsedSequence]:
        reader = csv.DictReader(io.StringIO(text))
        for row in reader:
            yield self._build(row, context)

    def _build(self, row: dict[str, Any], context: ImportContext) -> ParsedSequence:
        sci = _clean(row.get("organism"))
        organism = None
        if sci:
            organism = ParsedOrganism(
                scientific_name=sci,
                tax_id=_to_int(row.get("tax_id")) or 0,
                common_name=_clean(row.get("common_name")),
                group=_clean(row.get("group")),
                rank=_clean(row.get("rank")),
                lineage=_to_list(row.get("lineage")),
            )

        ps = ParsedSequence(
            seq_type=_clean(row.get("seq_type")) or (context.seq_type or ""),
            accession=_clean(row.get("accession")) or "",
            name=_clean(row.get("name")) or "",
            organism=organism,  # type: ignore[arg-type]
            source_key=_clean(row.get("source")) or _clean(row.get("source_key")) or context.source_key,
            source_name=context.source_name,
            version=_clean(row.get("version")),
            description=_clean(row.get("description")),
            molecule=_clean(row.get("molecule")),
            residues=_clean(row.get("sequence")) or _clean(row.get("residues")),
            length=_to_int(row.get("length")),
            gc_content=_to_float(row.get("gc_content")),
            molecule_type=_clean(row.get("molecule_type")),
            strand=_clean(row.get("strand")),
            rna_class=_clean(row.get("rna_class")),
            is_coding=_to_bool(row.get("is_coding")),
            gene=_clean(row.get("gene")),
            reviewed=_to_bool(row.get("reviewed")),
            molecular_weight=_to_float(row.get("molecular_weight")),
            function=_clean(row.get("function")),
            pdb_ids=_to_list(row.get("pdb_ids")),
            domains=_to_list(row.get("domains")),
            cas_system=_clean(row.get("cas_system")),
            target_gene=_clean(row.get("target_gene")),
            pam=_clean(row.get("pam")),
            genomic_target=_clean(row.get("genomic_target")),
            on_target_score=_to_float(row.get("on_target_score")),
            off_target_score=_to_float(row.get("off_target_score")),
            family=_clean(row.get("family")),
            host=_clean(row.get("host")),
            genome_type=_clean(row.get("genome_type")),
            segment=_clean(row.get("segment")),
        )
        return self._apply_context(ps, context)
