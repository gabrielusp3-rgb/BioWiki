from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from app.models.enums import CasSystem, DnaMoleculeType, GenomeType, RnaClass, Strand
from app.schemas.common import CamelModel


class SequenceBase(CamelModel):
    id: uuid.UUID
    type: str
    accession: str
    version: str | None = None
    name: str
    organism: str
    tax_id: int | None = None
    source: str
    length: int
    updated_at: datetime | None = None
    sequence: str | None = None
    description: str | None = None
    gene_name: str | None = None
    chromosome: str | None = None
    source_url: str | None = None
    annotations: dict[str, Any] | None = None


class DnaRead(SequenceBase):
    molecule_type: DnaMoleculeType | None = None
    strand: Strand | None = None
    gc_content: float | None = None


class RnaRead(SequenceBase):
    rna_class: RnaClass
    is_coding: bool
    gc_content: float | None = None


class ProteinRead(SequenceBase):
    gene: str | None = None
    reviewed: bool
    molecular_weight: float | None = None
    function: str | None = None
    pdb_ids: list[str] = []
    domains: list[str] = []


class VirusRead(SequenceBase):
    family: str
    host: str | None = None
    genome_type: GenomeType
    segment: str | None = None
    molecule: str
    gc_content: float | None = None


class CrisprRead(CamelModel):
    id: uuid.UUID
    type: str = "crispr"
    accession: str
    name: str
    organism: str
    tax_id: int | None = None
    source: str
    system: CasSystem
    target_gene: str
    pam: str
    guide_length: int
    guide_sequence: str | None = None
    genomic_target: str | None = None
    on_target_score: float | None = None
    off_target_score: float | None = None
    updated_at: datetime | None = None
    description: str | None = None
    source_url: str | None = None
    gc_content: float | None = None
    annotations: dict[str, Any] | None = None
