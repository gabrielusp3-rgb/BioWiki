"""FASTA parser.

Header convention: ``>ACCESSION[.VERSION] free-text description``. Residues are
concatenated and upper-cased; whitespace is stripped. Organism/type are supplied
by the import context (FASTA does not carry them).
"""

from __future__ import annotations

from collections.abc import Iterator

from app.pipeline.models import ImportContext, ParsedSequence
from app.pipeline.parsers.base import BaseParser


class FastaParser(BaseParser):
    fmt = "fasta"

    def parse(self, text: str, context: ImportContext) -> Iterator[ParsedSequence]:
        header: str | None = None
        chunks: list[str] = []

        def _emit(hdr: str, seq_parts: list[str]) -> ParsedSequence:
            accession, _, description = hdr.partition(" ")
            accession = accession.strip()
            version = None
            if "." in accession:
                base, _, ver = accession.rpartition(".")
                if ver.isdigit():
                    accession, version = base, ver
            residues = "".join(seq_parts).replace(" ", "").replace("\r", "").upper()
            ps = ParsedSequence(
                seq_type=context.seq_type or "",
                accession=accession,
                name=description.strip() or accession,
                organism=None,  # type: ignore[arg-type]
                source_key=context.source_key,
                version=version,
                description=description.strip() or None,
                residues=residues or None,
            )
            return self._apply_context(ps, context)

        for raw in text.splitlines():
            line = raw.rstrip("\n")
            if line.startswith(">"):
                if header is not None:
                    yield _emit(header, chunks)
                header = line[1:].strip()
                chunks = []
            elif header is not None:
                chunks.append(line.strip())

        if header is not None:
            yield _emit(header, chunks)
