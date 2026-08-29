"""Validation of parsed records prior to persistence.

Guarantees scientific integrity: required provenance/identity fields must be
present and residues must belong to a valid biological alphabet. Invalid records
raise :class:`ValidationError` and are skipped by the worker — never fixed up
with fabricated values.
"""

from __future__ import annotations

from app.models.enums import (
    CasSystem,
    CrisprEvidenceType,
    DnaMoleculeType,
    GenomeType,
    Molecule,
    OrganismGroup,
    RnaClass,
    SequenceType,
    Strand,
)
from app.pipeline.errors import ValidationError
from app.pipeline.models import ParsedSequence

# IUPAC alphabets (uppercase). Nucleotide includes ambiguity codes and gap.
_NUCLEOTIDE = set("ACGTUNRYSWKMBDHV-")
_PROTEIN = set("ACDEFGHIKLMNPQRSTVWYBXZJUO*-")

_SEQ_TYPES = {t.value for t in SequenceType}
_MOLECULES = {m.value for m in Molecule}
_GROUPS = {g.value for g in OrganismGroup}
_DNA_TYPES = {t.value for t in DnaMoleculeType}
_STRANDS = {s.value for s in Strand}
_RNA_CLASSES = {c.value for c in RnaClass}
_CAS = {c.value for c in CasSystem}
_CRISPR_EVIDENCE = {c.value for c in CrisprEvidenceType}
_GENOME_TYPES = {g.value for g in GenomeType}

_NUCLEOTIDE_TYPES = {"dna", "rna", "crispr", "virus", "genome"}

# Semantic category × polymer. Virus and CRISPR are not a polymer type.
_COMPATIBLE_MOLECULE: dict[str, set[str]] = {
    "dna": {"dna"},
    "rna": {"rna"},
    "protein": {"protein"},
    "peptide": {"protein"},
    "virus": {"dna", "rna"},
    "crispr": {"dna", "rna"},
    "genome": {"dna", "rna"},
}

# NCBI bins that are real source labels but cannot be mapped onto OrganismGroup
# without inventing a kingdom-level classification. Records in these bins are
# rejected, never stored as bacteria/animal/etc.
_UNCLASSIFIABLE_TAXONOMY = (
    "synthetic construct",
    "artificial sequences",
    "unclassified sequences",
    "other sequences",
)


def normalize_lineage(lineage: list | None) -> list[str]:
    """Coerce source lineage payloads to scientific-name strings.

    UniProt returns lineage objects; GenBank returns semicolon-split names.
    Only real names supplied by the source are kept — nothing is invented.
    """
    names: list[str] = []
    for item in lineage or []:
        if isinstance(item, str) and item.strip():
            names.append(item.strip())
        elif isinstance(item, dict):
            name = item.get("scientificName") or item.get("name")
            if isinstance(name, str) and name.strip():
                names.append(name.strip())
    return names


def compute_gc(residues: str) -> float | None:
    """Real GC ratio (0–1) from actual residues; None if not applicable."""
    if not residues:
        return None
    seq = residues.upper()
    counts = {b: seq.count(b) for b in "ACGTU"}
    total = sum(counts.values())
    if total == 0:
        return None
    gc = counts["G"] + counts["C"]
    return round(gc / total, 4)


def pubmed_id_is_valid(pubmed_id: int | None) -> bool:
    """PubMed IDs are positive integers when present; None means 'not supplied'."""
    if pubmed_id is None:
        return True
    return isinstance(pubmed_id, int) and pubmed_id > 0


def source_taxonomy_is_unclassifiable(org) -> bool:
    """True when the source taxonomy cannot map onto OrganismGroup.

    Patent / synthetic / unclassified NCBI bins are real labels, but the current
    model only stores animal|plant|fungus|bacteria|archaea|virus|protozoan.
    Returning True means the record must be skipped — not forced into a kingdom.
    """
    if org is None:
        return False
    if infer_group_from_lineage(getattr(org, "lineage", None)):
        return False
    blob = " ".join(
        [getattr(org, "scientific_name", None) or ""]
        + normalize_lineage(getattr(org, "lineage", None))
    ).lower()
    return any(marker in blob for marker in _UNCLASSIFIABLE_TAXONOMY)


def infer_group_from_lineage(lineage: list | None) -> str | None:
    """Classify an organism group from its real NCBI/UniProt lineage (no invention)."""
    joined = " ".join(normalize_lineage(lineage)).lower()
    if not joined:
        return None
    if "virus" in joined or "viruses" in joined:
        return OrganismGroup.VIRUS.value
    if "archaea" in joined:
        return OrganismGroup.ARCHAEA.value
    if "bacteria" in joined:
        return OrganismGroup.BACTERIA.value
    if "fungi" in joined:
        return OrganismGroup.FUNGUS.value
    if "viridiplantae" in joined or "plantae" in joined:
        return OrganismGroup.PLANT.value
    if "metazoa" in joined:
        return OrganismGroup.ANIMAL.value
    if "eukaryota" in joined and "alveolata" in joined:
        return OrganismGroup.PROTOZOAN.value
    if "eukaryota" in joined and ("euglenozoa" in joined or "apicomplexa" in joined):
        return OrganismGroup.PROTOZOAN.value
    return None


def _require(condition: bool, message: str, field: str | None = None) -> None:
    if not condition:
        raise ValidationError(message, field=field)


def validate(ps: ParsedSequence) -> None:
    # Identity / provenance
    _require(bool(ps.accession and ps.accession.strip()), "accession is required", "accession")
    _require(bool(ps.name and ps.name.strip()), "name is required", "name")
    _require(ps.seq_type in _SEQ_TYPES, f"invalid seq_type: {ps.seq_type!r}", "seq_type")
    _require(bool(ps.source_key and ps.source_key.strip()), "source_key is required", "source_key")

    # Organism
    org = ps.organism
    _require(org is not None, "organism is required", "organism")
    _require(bool(org.scientific_name and org.scientific_name.strip()),
             "organism.scientific_name is required", "organism.scientific_name")
    _require(isinstance(org.tax_id, int) and org.tax_id > 0,
             "organism.tax_id must be a positive integer", "organism.tax_id")
    if org.group is not None:
        _require(org.group in _GROUPS,
                 f"organism.group must be one of {_GROUPS}", "organism.group")
    elif source_taxonomy_is_unclassifiable(org):
        raise ValidationError(
            "source taxonomy is synthetic or unclassified; "
            "OrganismGroup cannot be assigned without inventing a classification",
            field="organism.group",
        )
    else:
        raise ValidationError(
            "organism.group could not be determined from source taxonomy; "
            "refusing to invent a kingdom",
            field="organism.group",
        )

    # Molecule — compatible with the semantic category, not inferred from alphabet.
    if ps.molecule is not None:
        _require(ps.molecule in _MOLECULES, f"invalid molecule: {ps.molecule!r}", "molecule")
        allowed = _COMPATIBLE_MOLECULE.get(ps.seq_type)
        if allowed is not None:
            _require(
                ps.molecule in allowed,
                f"molecule {ps.molecule!r} is incompatible with seq_type {ps.seq_type!r}",
                "molecule",
            )
    elif ps.seq_type in {"dna", "rna", "protein", "peptide", "virus"}:
        raise ValidationError(
            f"{ps.seq_type} requires an official molecule type",
            field="molecule",
        )

    # Length / residues
    length = ps.effective_length()
    _require(length > 0, "length must be > 0 (provide residues or length)", "length")

    if ps.residues:
        alphabet = _PROTEIN if ps.seq_type in {"protein", "peptide"} else _NUCLEOTIDE
        invalid = set(ps.residues.upper()) - alphabet
        _require(not invalid, f"residues contain invalid symbols: {sorted(invalid)}", "residues")
        # Long ACGT-only strings stored as protein are nucleotide sequences, not peptides.
        if ps.seq_type in {"protein", "peptide"}:
            symbols = set(ps.residues.upper())
            if len(ps.residues) >= 80 and symbols and symbols <= set("ACGTN"):
                raise ValidationError(
                    "protein residues match a nucleotide alphabet",
                    field="residues",
                )

    if ps.gc_content is not None:
        _require(0.0 <= ps.gc_content <= 1.0, "gc_content must be within 0–1", "gc_content")

    # Per-type feature requirements
    if ps.seq_type == "dna":
        _require(ps.molecule_type in _DNA_TYPES, "dna requires a valid molecule_type", "molecule_type")
        if ps.strand is not None:
            _require(ps.strand in _STRANDS, "invalid strand", "strand")
    elif ps.seq_type == "rna":
        _require(ps.rna_class in _RNA_CLASSES, "rna requires a valid rna_class", "rna_class")
    elif ps.seq_type == "crispr":
        _require(ps.cas_system in _CAS, "crispr requires a valid cas_system", "cas_system")
        if ps.evidence_type is None:
            ps.evidence_type = CrisprEvidenceType.NATURAL_CRISPR_ELEMENT.value
        _require(
            ps.evidence_type in _CRISPR_EVIDENCE,
            "crispr requires a valid evidence_type",
            "evidence_type",
        )
        if ps.evidence_type == CrisprEvidenceType.COMPUTATIONAL_TARGET.value:
            _require(
                bool(ps.target_source_accession and ps.target_source_accession.strip()),
                "computational CRISPR requires the authentic target accession",
                "target_source_accession",
            )
            _require(
                isinstance(ps.target_tax_id, int) and ps.target_tax_id > 0,
                "computational CRISPR requires the target TaxID",
                "target_tax_id",
            )
            _require(
                bool(ps.method and ps.method.strip()),
                "computational CRISPR requires the implemented method name",
                "method",
            )
            _require(
                ps.on_target_score is None and ps.off_target_score is None,
                "computational CRISPR must not invent efficiency scores",
                "on_target_score",
            )
        if ps.evidence_type == CrisprEvidenceType.EXPERIMENTAL_GUIDE.value:
            _require(
                ps.source_pmid is not None or bool(ps.source_url),
                "experimental CRISPR requires a publication or source URL",
                "source_pmid",
            )
    elif ps.seq_type == "virus":
        _require(bool(ps.family and ps.family.strip()), "virus requires a family", "family")
        _require(ps.genome_type in _GENOME_TYPES, "virus requires a valid genome_type", "genome_type")
    elif ps.seq_type in {"protein", "peptide"}:
        _require(ps.reviewed is not None, "protein requires a reviewed flag", "reviewed")


def enrich(ps: ParsedSequence) -> ParsedSequence:
    """Fill deterministic, real derived values (GC, length, group) in place."""
    if ps.length is None and ps.residues:
        ps.length = len(ps.residues)
    if (
        ps.gc_content is None
        and ps.residues
        and ps.seq_type in _NUCLEOTIDE_TYPES
    ):
        ps.gc_content = compute_gc(ps.residues)
    if ps.organism:
        if ps.organism.lineage:
            ps.organism.lineage = normalize_lineage(ps.organism.lineage)
        if ps.organism.group is None and ps.organism.lineage:
            ps.organism.group = infer_group_from_lineage(ps.organism.lineage)
    if ps.seq_type == "dna" and ps.strand is None:
        ps.strand = Strand.UNKNOWN.value
    # Messenger RNA is coding by definition — a deterministic biological fact.
    if ps.seq_type == "rna" and ps.is_coding is None and ps.rna_class == "mrna":
        ps.is_coding = True
    return ps
