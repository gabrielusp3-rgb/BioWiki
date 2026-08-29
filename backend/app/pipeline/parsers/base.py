"""Parser interface.

A parser turns a source document into an iterator of :class:`ParsedSequence`,
applying the :class:`ImportContext` for provenance/classification the format
does not carry. Parsers must not invent biological content.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator

from app.pipeline.models import ImportContext, ParsedOrganism, ParsedSequence


class BaseParser(ABC):
    #: Short format key, e.g. "fasta".
    fmt: str = "base"

    @abstractmethod
    def parse(self, text: str, context: ImportContext) -> Iterator[ParsedSequence]:
        """Yield parsed records from ``text``."""
        raise NotImplementedError

    @staticmethod
    def _apply_context(ps: ParsedSequence, context: ImportContext) -> ParsedSequence:
        """Fill missing provenance/classification from the import context."""
        if not ps.source_key:
            ps.source_key = context.source_key
        if ps.source_name is None:
            ps.source_name = context.source_name
        if ps.seq_type is None or ps.seq_type == "":
            ps.seq_type = context.seq_type or ""
        if ps.molecule is None:
            ps.molecule = context.molecule
        if ps.organism is None and context.organism is not None:
            ps.organism = _clone_org(context.organism)

        # Per-type classification defaults (only when the record omits them).
        if ps.molecule_type is None:
            ps.molecule_type = context.molecule_type
        if ps.strand is None:
            ps.strand = context.strand
        if ps.rna_class is None:
            ps.rna_class = context.rna_class
        if ps.is_coding is None:
            ps.is_coding = context.is_coding
        if ps.reviewed is None:
            ps.reviewed = context.reviewed
        if ps.cas_system is None:
            ps.cas_system = context.cas_system
        if ps.evidence_type is None:
            ps.evidence_type = context.evidence_type
        if ps.genome_type is None:
            ps.genome_type = context.genome_type
        if ps.family is None:
            ps.family = context.family
        if ps.host is None:
            ps.host = context.host
        return ps


def _clone_org(org: ParsedOrganism) -> ParsedOrganism:
    return ParsedOrganism(
        scientific_name=org.scientific_name,
        tax_id=org.tax_id,
        common_name=org.common_name,
        group=org.group,
        rank=org.rank,
        lineage=list(org.lineage),
        image_url=org.image_url,
    )
