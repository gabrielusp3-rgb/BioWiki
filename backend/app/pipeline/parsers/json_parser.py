"""JSON parser for BIOWIKI's canonical import schema.

Accepts either a top-level array of records or an object ``{"records": [...]}``.
Each record maps directly onto :class:`ParsedSequence` fields (snake_case), with
the organism as a nested object or a flat ``organism`` + ``tax_id`` pair.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Any

from app.pipeline.errors import ParseError
from app.pipeline.models import ImportContext, ParsedOrganism, ParsedSequence, ParsedXref
from app.pipeline.parsers.base import BaseParser


class JsonParser(BaseParser):
    fmt = "json"

    def parse(self, text: str, context: ImportContext) -> Iterator[ParsedSequence]:
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ParseError(f"Invalid JSON: {exc}") from exc

        if isinstance(payload, dict):
            records = payload.get("records", [])
        elif isinstance(payload, list):
            records = payload
        else:
            raise ParseError("JSON must be an array or an object with a 'records' array.")

        for item in records:
            if not isinstance(item, dict):
                raise ParseError("Each record must be a JSON object.")
            yield self._build(item, context)

    def _build(self, item: dict[str, Any], context: ImportContext) -> ParsedSequence:
        organism = self._organism(item)
        xrefs = [
            ParsedXref(
                db_name=x.get("db_name", ""),
                external_id=x.get("external_id", ""),
                url=x.get("url"),
            )
            for x in item.get("cross_references", [])
            if isinstance(x, dict)
        ]
        ps = ParsedSequence(
            seq_type=item.get("seq_type") or (context.seq_type or ""),
            accession=item.get("accession", ""),
            name=item.get("name", ""),
            organism=organism,  # type: ignore[arg-type]
            source_key=item.get("source_key") or context.source_key,
            source_name=item.get("source_name") or context.source_name,
            version=item.get("version"),
            description=item.get("description"),
            molecule=item.get("molecule"),
            residues=item.get("residues") or item.get("sequence"),
            length=item.get("length"),
            gc_content=item.get("gc_content"),
            molecule_type=item.get("molecule_type"),
            strand=item.get("strand"),
            rna_class=item.get("rna_class"),
            is_coding=item.get("is_coding"),
            gene=item.get("gene"),
            reviewed=item.get("reviewed"),
            molecular_weight=item.get("molecular_weight"),
            function=item.get("function"),
            pdb_ids=list(item.get("pdb_ids", []) or []),
            domains=list(item.get("domains", []) or []),
            cas_system=item.get("cas_system"),
            target_gene=item.get("target_gene"),
            pam=item.get("pam"),
            genomic_target=item.get("genomic_target"),
            on_target_score=item.get("on_target_score"),
            off_target_score=item.get("off_target_score"),
            family=item.get("family"),
            host=item.get("host"),
            genome_type=item.get("genome_type"),
            segment=item.get("segment"),
            cross_references=xrefs,
        )
        return self._apply_context(ps, context)

    @staticmethod
    def _organism(item: dict[str, Any]) -> ParsedOrganism | None:
        org = item.get("organism")
        if isinstance(org, dict):
            return ParsedOrganism(
                scientific_name=org.get("scientific_name", ""),
                tax_id=int(org.get("tax_id", 0) or 0),
                common_name=org.get("common_name"),
                group=org.get("group"),
                rank=org.get("rank"),
                lineage=list(org.get("lineage", []) or []),
                image_url=org.get("image_url"),
            )
        if isinstance(org, str) and org:
            return ParsedOrganism(
                scientific_name=org,
                tax_id=int(item.get("tax_id", 0) or 0),
                common_name=item.get("common_name"),
                group=item.get("group"),
                lineage=list(item.get("lineage", []) or []),
            )
        return None
