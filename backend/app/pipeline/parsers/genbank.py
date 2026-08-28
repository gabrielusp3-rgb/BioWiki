"""GenBank flat-file parser (common fields + bibliography).

Parses LOCUS, DEFINITION, ACCESSION, VERSION, SOURCE/ORGANISM, REFERENCE
blocks (AUTHORS/TITLE/JOURNAL/PUBMED) and ORIGIN from one or more records
(``//`` separated). Also extracts real feature qualifiers: ``/gene=``,
``/chromosome=`` and the LOCUS modification date. Sequence type/molecule are
inferred from the LOCUS line when the import context does not override them.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from datetime import datetime, timezone

from app.pipeline.models import (
    ImportContext,
    ParsedOrganism,
    ParsedPublication,
    ParsedSequence,
)
from app.pipeline.parsers.base import BaseParser

_TAXON_RE = re.compile(r'/db_xref="taxon:(\d+)"')
_GENE_RE = re.compile(r'/gene="([^"]+)"')
_CHROMOSOME_RE = re.compile(r'/chromosome="([^"]+)"')
_HOST_RE = re.compile(r'/(?:lab_)?host="([^"]+)"')
_PRODUCT_RE = re.compile(r'/product="([^"]+)"')
_TOPOLOGY_RE = re.compile(r"\b(linear|circular)\b", re.IGNORECASE)

# LOCUS strandedness descriptor → virus genome type (explicit in the record).
_GENOME_TYPE_BY_MOLECULE = {
    "ds-DNA": "dsDNA",
    "ss-DNA": "ssDNA",
    "ds-RNA": "dsRNA",
    "DNA": "dsDNA",  # GenBank viral DNA records default to double-stranded
}

# ICTV taxa whose membership determines the Baltimore group — real taxonomy,
# not a guess: Negarnaviricota is by definition the negative-sense RNA phylum,
# Kitrinoviricota/Pisoniviricetes are positive-sense, Retroviridae is ssRNA-RT
# and Hepadnaviridae is dsDNA-RT.
_GENOME_TYPE_BY_LINEAGE = [
    ("retroviridae", "ssRNA-RT"),
    ("hepadnaviridae", "dsDNA-RT"),
    ("negarnaviricota", "ssRNA-"),
    ("kitrinoviricota", "ssRNA+"),
    ("pisoniviricetes", "ssRNA+"),
    ("leviviricetes", "ssRNA+"),
]

# Cas system mentioned in the record definition (real text, no guessing).
_CAS_PATTERNS = [
    (re.compile(r"cas9", re.IGNORECASE), "cas9"),
    (re.compile(r"cas12a|cpf1", re.IGNORECASE), "cas12a"),
    (re.compile(r"cas13", re.IGNORECASE), "cas13"),
    (re.compile(r"base editor|base-editor", re.IGNORECASE), "base_editor"),
]
_LOCUS_DATE_RE = re.compile(r"(\d{2}-[A-Z]{3}-\d{4})\s*$")
_JOURNAL_YEAR_RE = re.compile(r"\((\d{4})\)\s*\.?\s*$")
_JOURNAL_PAGES_RE = re.compile(r",\s*([0-9A-Za-z]+(?:-[0-9A-Za-z]+))\s*\(\d{4}\)")
_JOURNAL_VOLUME_RE = re.compile(r"\s(\d+[A-Za-z]?)\s*(?:\([^)]*\))?\s*,")


class GenBankParser(BaseParser):
    fmt = "genbank"

    def parse(self, text: str, context: ImportContext) -> Iterator[ParsedSequence]:
        for block in self._split_records(text):
            record = self._parse_record(block, context)
            if record is not None:
                yield record

    @staticmethod
    def _split_records(text: str) -> Iterator[list[str]]:
        buffer: list[str] = []
        for line in text.splitlines():
            if line.strip() == "//":
                if buffer:
                    yield buffer
                buffer = []
            else:
                buffer.append(line)
        if buffer and any(l.strip() for l in buffer):
            yield buffer

    def _parse_record(self, lines: list[str], context: ImportContext) -> ParsedSequence | None:
        origin_idx = next((i for i, l in enumerate(lines) if l.startswith("ORIGIN")), None)
        header = lines[:origin_idx] if origin_idx is not None else lines
        residues = ""
        if origin_idx is not None:
            residues = self._parse_origin(lines[origin_idx + 1:])

        locus_name, length, gb_molecule, unit = "", None, "", ""
        accession = version = definition = ""
        sci_name = ""
        lineage: list[str] = []
        source_date: datetime | None = None
        publications: list[ParsedPublication] = []
        keywords = ""
        topology = ""
        contig = ""

        i = 0
        while i < len(header):
            line = header[i]
            if not line or line[0] == " ":
                i += 1
                continue
            key = line[:12].strip()
            value = line[12:].strip()

            if key == "LOCUS":
                locus_name, length, gb_molecule, unit = self._parse_locus(line)
                source_date = self._parse_locus_date(line)
                topology = self._parse_topology(line)
            elif key == "DEFINITION":
                definition, i = self._collect(header, i, value)
                continue
            elif key == "KEYWORDS":
                keywords, i = self._collect(header, i, value)
                continue
            elif key == "ACCESSION":
                accession = value.split()[0] if value else ""
            elif key == "VERSION":
                token = value.split()[0] if value else ""
                if "." in token:
                    accession_v, _, ver = token.rpartition(".")
                    accession = accession or accession_v
                    version = ver
            elif key == "SOURCE":
                sci_name, lineage, i = self._parse_source(header, i)
                continue
            elif key == "REFERENCE":
                publication, i = self._parse_reference(header, i)
                if publication is not None:
                    publication.reference_order = len(publications) + 1
                    publications.append(publication)
                continue
            elif key == "CONTIG":
                contig, i = self._collect(header, i, value)
                continue
            i += 1

        if not accession and locus_name:
            accession = locus_name
        if not accession:
            return None

        seq_type, molecule = GenBankParser._infer_type(context, gb_molecule, unit)
        organism = None
        if sci_name:
            taxon_match = _TAXON_RE.search("\n".join(header))
            tax_id = int(taxon_match.group(1)) if taxon_match else 0
            organism = ParsedOrganism(
                scientific_name=sci_name,
                tax_id=tax_id,  # real taxon from /db_xref; 0 (skipped) if absent
                lineage=lineage,
            )

        body = "\n".join(header)
        gene_match = _GENE_RE.search(body)
        chromosome_match = _CHROMOSOME_RE.search(body)
        product_match = _PRODUCT_RE.search(body)

        # Real record metadata copied verbatim from the flat file (no invention).
        annotations: dict[str, str] = {}
        if gb_molecule:
            annotations["Molecule type"] = gb_molecule
        if topology:
            annotations["Topology"] = topology
        cleaned_keywords = keywords.strip().rstrip(".")
        if cleaned_keywords:
            annotations["Keywords"] = cleaned_keywords
        if product_match:
            annotations["Product"] = product_match.group(1)
        if contig:
            annotations["CONTIG"] = contig

        ps = ParsedSequence(
            seq_type=seq_type or (context.seq_type or ""),
            accession=accession,
            name=definition or locus_name or accession,
            organism=organism,  # type: ignore[arg-type]
            source_key=context.source_key,
            source_name=context.source_name,
            version=version or None,
            description=definition or None,
            molecule=molecule,
            residues=residues or None,
            length=length,
            source_updated_at=source_date,
            gene_name=gene_match.group(1) if gene_match else None,
            chromosome=chromosome_match.group(1) if chromosome_match else None,
            annotations=annotations or None,
            publications=publications,
        )

        # Real classification derived from the LOCUS molecule descriptor.
        if ps.seq_type == "dna":
            ps.molecule_type = "mrna" if "mRNA" in gb_molecule else "genomic"
        elif ps.seq_type == "rna":
            ps.rna_class = self._classify_rna(gb_molecule, definition)
        elif ps.seq_type == "virus":
            # Family: the real taxon ending in "viridae" from the record lineage.
            family = next((t for t in lineage if t.lower().endswith("viridae")), None)
            ps.family = family
            ps.genome_type = self._virus_genome_type(gb_molecule, lineage)
            # Stored residue alphabet, straight from the LOCUS descriptor.
            ps.molecule = "rna" if "RNA" in gb_molecule else "dna"
            host_match = _HOST_RE.search(body)
            ps.host = host_match.group(1) if host_match else None
        elif ps.seq_type == "crispr":
            for pattern, system in _CAS_PATTERNS:
                if pattern.search(definition or ""):
                    ps.cas_system = system
                    break
            else:
                ps.cas_system = "other"
            if ps.gene_name:
                ps.target_gene = ps.gene_name

        return self._apply_context(ps, context)

    @staticmethod
    def _virus_genome_type(gb_molecule: str, lineage: list[str]) -> str:
        """Baltimore group from the record's own lineage and LOCUS descriptor."""
        joined = " ".join(lineage).lower()
        for taxon, genome_type in _GENOME_TYPE_BY_LINEAGE:
            if taxon in joined:
                return genome_type
        return _GENOME_TYPE_BY_MOLECULE.get(gb_molecule, "other")

    @staticmethod
    def _classify_rna(gb_molecule: str, definition: str) -> str:
        """RNA class from the LOCUS descriptor and the record's own definition."""
        if "mRNA" in gb_molecule:
            return "mrna"
        text = (definition or "").lower()
        if "ribosomal rna" in text or "rrna" in text:
            return "rrna"
        if "transfer rna" in text or "trna" in text:
            return "trna"
        if "long non-coding" in text or "lncrna" in text or "long intergenic" in text:
            return "lncrna"
        if "microrna" in text or "mir-" in text:
            return "mirna"
        if "small nuclear rna" in text or "snrna" in text:
            return "snrna"
        return "other"

    @staticmethod
    def _parse_locus(line: str) -> tuple[str, int | None, str, str]:
        parts = line.split()
        name = parts[1] if len(parts) > 1 else ""
        length: int | None = None
        unit = ""
        molecule = ""
        for idx, tok in enumerate(parts):
            if tok.isdigit() and idx + 1 < len(parts) and parts[idx + 1] in {"bp", "aa"}:
                length = int(tok)
                unit = parts[idx + 1]
            if "RNA" in tok or "DNA" in tok:
                molecule = tok
        return name, length, molecule, unit

    @staticmethod
    def _collect(lines: list[str], start: int, first: str) -> tuple[str, int]:
        collected = [first]
        j = start + 1
        while j < len(lines) and lines[j].startswith(" "):
            # stop if a nested key like ORGANISM appears (handled elsewhere)
            collected.append(lines[j].strip())
            j += 1
        return " ".join(p for p in collected if p).strip(), j

    @staticmethod
    def _parse_source(lines: list[str], start: int) -> tuple[str, list[str], int]:
        sci_name = ""
        lineage: list[str] = []
        j = start + 1
        while j < len(lines) and lines[j].startswith(" "):
            stripped = lines[j].strip()
            if stripped.startswith("ORGANISM"):
                sci_name = stripped[len("ORGANISM"):].strip()
                j += 1
                lineage_parts: list[str] = []
                while j < len(lines) and lines[j].startswith(" ") and not lines[j][:12].strip():
                    lineage_parts.append(lines[j].strip())
                    j += 1
                joined = " ".join(lineage_parts).rstrip(".")
                lineage = [t.strip() for t in joined.split(";") if t.strip()]
                break
            j += 1
        return sci_name, lineage, j

    @staticmethod
    def _collect_sub(lines: list[str], start: int, first: str) -> tuple[str, int]:
        """Collect a sub-key value inside a REFERENCE block.

        Continuation lines are fully indented (blank key column); the next
        sub-key (AUTHORS/TITLE/JOURNAL/PUBMED…) has text within the first 12
        columns and must NOT be swallowed.
        """
        collected = [first]
        j = start + 1
        while (
            j < len(lines)
            and lines[j].startswith(" ")
            and not lines[j][:12].strip()
        ):
            collected.append(lines[j].strip())
            j += 1
        return " ".join(p for p in collected if p).strip(), j

    @staticmethod
    def _parse_locus_date(line: str) -> datetime | None:
        match = _LOCUS_DATE_RE.search(line)
        if not match:
            return None
        try:
            return datetime.strptime(match.group(1), "%d-%b-%Y").replace(
                tzinfo=timezone.utc
            )
        except ValueError:
            return None

    @staticmethod
    def _parse_topology(line: str) -> str:
        """Molecule topology (linear/circular) as stated on the LOCUS line."""
        match = _TOPOLOGY_RE.search(line)
        return match.group(1).lower() if match else ""

    @staticmethod
    def _parse_reference(lines: list[str], start: int) -> tuple[ParsedPublication | None, int]:
        """Parse one REFERENCE block (AUTHORS, TITLE, JOURNAL, PUBMED).

        Only real values present in the record are kept; blocks without a title
        or PubMed ID (e.g. 'Direct Submission') are dropped.
        """
        authors_raw = title = journal_raw = ""
        pubmed_id: int | None = None

        j = start + 1
        while j < len(lines) and (not lines[j] or lines[j][0] == " "):
            sub_key = lines[j][:12].strip()
            sub_value = lines[j][12:].strip()
            if sub_key == "AUTHORS":
                authors_raw, j = GenBankParser._collect_sub(lines, j, sub_value)
                continue
            if sub_key == "TITLE":
                title, j = GenBankParser._collect_sub(lines, j, sub_value)
                continue
            if sub_key == "JOURNAL":
                journal_raw, j = GenBankParser._collect_sub(lines, j, sub_value)
                continue
            if sub_key == "PUBMED":
                if sub_value.isdigit():
                    pubmed_id = int(sub_value)
            j += 1

        if not pubmed_id and (not title or title.lower() == "direct submission"):
            return None, j

        year: int | None = None
        volume = pages = None
        journal = journal_raw or None
        if journal_raw:
            year_match = _JOURNAL_YEAR_RE.search(journal_raw)
            if year_match:
                year = int(year_match.group(1))
            pages_match = _JOURNAL_PAGES_RE.search(journal_raw)
            if pages_match:
                pages = pages_match.group(1)
            volume_match = _JOURNAL_VOLUME_RE.search(journal_raw)
            if volume_match:
                volume = volume_match.group(1)
                journal = journal_raw[: volume_match.start()].strip() or None

        # GenBank separates authors with ", " / " and "; surname and initials
        # are joined by a comma without a space (e.g. ``Bell,G.I.``).
        authors = (
            [a.strip() for a in re.split(r",\s+|\s+and\s+", authors_raw) if a.strip()]
            if authors_raw
            else []
        )
        url = f"https://pubmed.ncbi.nlm.nih.gov/{pubmed_id}/" if pubmed_id else None

        return (
            ParsedPublication(
                title=title or None,
                pubmed_id=pubmed_id,
                authors=authors,
                journal=journal,
                year=year,
                volume=volume,
                pages=pages,
                url=url,
            ),
            j,
        )

    @staticmethod
    def _parse_origin(lines: list[str]) -> str:
        residues: list[str] = []
        for line in lines:
            if line.strip() == "//":
                break
            residues.append("".join(ch for ch in line if ch.isalpha()))
        return "".join(residues).upper()

    @staticmethod
    def _locus_classification(gb_molecule: str, unit: str) -> tuple[str | None, str | None]:
        """Polymer class from the LOCUS line (official GenBank fields)."""
        if unit == "aa":
            return "protein", "protein"
        if "RNA" in (gb_molecule or ""):
            return "rna", "rna"
        if gb_molecule:
            return "dna", "dna"
        return None, None

    @staticmethod
    def _infer_type(context: ImportContext, gb_molecule: str, unit: str) -> tuple[str, str | None]:
        """Semantic category from the operator context, polymer from the LOCUS.

        Virus/CRISPR/genome stay as catalogue categories even when the LOCUS
        molecule is DNA or RNA. DNA/RNA/protein follow the official LOCUS so an
        import job labelled ``dna`` cannot store an mRNA transcript as DNA.
        """
        locus_type, locus_mol = GenBankParser._locus_classification(gb_molecule, unit)
        semantic = {"virus", "crispr", "genome"}
        if context.seq_type in semantic:
            return context.seq_type, context.molecule or locus_mol
        if locus_type:
            return locus_type, locus_mol
        if context.seq_type:
            return context.seq_type, context.molecule
        return "dna", "dna"
