"""Normalized intermediate representation used across the pipeline.

Parsers emit :class:`ParsedSequence` objects; validators check them; importers
persist them. This decouples every source format from the database models.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ParsedOrganism:
    scientific_name: str
    tax_id: int
    common_name: str | None = None
    group: str | None = None            # OrganismGroup value
    rank: str | None = None
    lineage: list[str] = field(default_factory=list)
    image_url: str | None = None


@dataclass
class ParsedXref:
    db_name: str
    external_id: str
    url: str | None = None


@dataclass
class ParsedPublication:
    """Bibliographic reference extracted from a real source record.

    At least one verifiable identifier or a title must be present; records
    without any are dropped by the importer rather than filled in.
    """

    title: str | None = None
    pubmed_id: int | None = None
    doi: str | None = None
    pmc_id: str | None = None
    abstract: str | None = None
    authors: list[str] = field(default_factory=list)
    journal: str | None = None
    year: int | None = None
    volume: str | None = None
    pages: str | None = None
    url: str | None = None
    reference_order: int | None = None


@dataclass
class ParsedGenome:
    """Genome assembly record parsed from a real source (e.g. NCBI Datasets)."""

    accession: str
    organism: ParsedOrganism
    source_key: str
    source_name: str | None = None
    assembly_name: str | None = None
    assembly_level: str | None = None    # AssemblyLevel value
    description: str | None = None
    total_length: int | None = None
    chromosome_count: int | None = None
    scaffold_count: int | None = None
    contig_count: int | None = None
    gc_content: float | None = None
    release_date: str | None = None      # ISO date string from the source
    source_url: str | None = None
    annotations: dict | None = None


@dataclass
class ParsedSequence:
    # Core
    seq_type: str                        # SequenceType value
    accession: str
    name: str
    organism: ParsedOrganism
    source_key: str
    source_name: str | None = None
    version: str | None = None
    description: str | None = None
    molecule: str | None = None          # Molecule value (dna|rna|protein)
    residues: str | None = None
    length: int | None = None
    gc_content: float | None = None
    source_updated_at: datetime | None = None

    # DNA
    molecule_type: str | None = None     # DnaMoleculeType value
    strand: str | None = None            # Strand value

    # RNA
    rna_class: str | None = None
    is_coding: bool | None = None

    # Protein
    gene: str | None = None
    reviewed: bool | None = None
    molecular_weight: float | None = None
    function: str | None = None
    pdb_ids: list[str] = field(default_factory=list)
    domains: list[str] = field(default_factory=list)

    # CRISPR
    cas_system: str | None = None
    evidence_type: str | None = None
    target_gene: str | None = None
    pam: str | None = None
    genomic_target: str | None = None
    on_target_score: float | None = None
    off_target_score: float | None = None
    target_source_accession: str | None = None
    target_tax_id: int | None = None
    source_pmid: int | None = None
    method: str | None = None

    # Virus
    family: str | None = None
    host: str | None = None
    genome_type: str | None = None
    segment: str | None = None

    # Gene / genomic context (real metadata from the source record)
    gene_name: str | None = None
    chromosome: str | None = None

    # Canonical URL of the record at its source database.
    source_url: str | None = None
    # Structured annotations copied verbatim from the source (never invented).
    annotations: dict | None = None

    cross_references: list[ParsedXref] = field(default_factory=list)
    publications: list[ParsedPublication] = field(default_factory=list)

    def effective_length(self) -> int:
        if self.residues:
            return len(self.residues)
        return int(self.length or 0)

    def checksum(self) -> str | None:
        if not self.residues:
            return None
        return hashlib.sha256(self.residues.encode("ascii", "ignore")).hexdigest()


@dataclass
class ImportContext:
    """Defaults applied to records that do not carry them (e.g. plain FASTA).

    Set by the operator per dataset — never invents biological content, only
    supplies provenance/classification that the file format omits.
    """

    source_key: str
    source_name: str | None = None
    seq_type: str | None = None
    molecule: str | None = None
    organism: ParsedOrganism | None = None

    # Per-type classification defaults for formats that omit them (e.g. FASTA).
    # These are operator-provided provenance/classification, not invented content.
    molecule_type: str | None = None    # DNA
    strand: str | None = None           # DNA
    rna_class: str | None = None        # RNA
    is_coding: bool | None = None       # RNA
    reviewed: bool | None = None        # Protein
    cas_system: str | None = None       # CRISPR
    evidence_type: str | None = None    # CRISPR evidence class
    genome_type: str | None = None      # Virus
    family: str | None = None           # Virus
    host: str | None = None             # Virus


@dataclass
class ImportReport:
    total: int = 0
    created: int = 0
    updated: int = 0
    skipped: int = 0
    failed: int = 0
    errors: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "total": self.total,
            "created": self.created,
            "updated": self.updated,
            "skipped": self.skipped,
            "failed": self.failed,
            "errors": self.errors,
        }
