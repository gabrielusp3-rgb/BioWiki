"""Per-type feature tables (one row per sequence) and protein child tables."""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.enums import (
    CAS_SYSTEM_ENUM,
    CRISPR_EVIDENCE_TYPE_ENUM,
    DNA_MOLECULE_TYPE_ENUM,
    GENOME_TYPE_ENUM,
    RNA_CLASS_ENUM,
    STRAND_ENUM,
    CasSystem,
    CrisprEvidenceType,
    DnaMoleculeType,
    GenomeType,
    RnaClass,
    Strand,
)
from app.models.mixins import UUIDPrimaryKeyMixin

_SEQ_FK = lambda: mapped_column(  # noqa: E731
    PGUUID(as_uuid=True),
    ForeignKey("sequences.id", ondelete="CASCADE"),
    primary_key=True,
)


class DnaFeature(Base):
    __tablename__ = "dna_features"

    sequence_id: Mapped[uuid.UUID] = _SEQ_FK()
    molecule_type: Mapped[DnaMoleculeType] = mapped_column(
        DNA_MOLECULE_TYPE_ENUM, nullable=False, index=True
    )
    strand: Mapped[Strand] = mapped_column(
        STRAND_ENUM, nullable=False, default=Strand.UNKNOWN
    )


class RnaFeature(Base):
    __tablename__ = "rna_features"

    sequence_id: Mapped[uuid.UUID] = _SEQ_FK()
    rna_class: Mapped[RnaClass] = mapped_column(
        RNA_CLASS_ENUM, nullable=False, index=True
    )
    is_coding: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class ProteinFeature(Base):
    __tablename__ = "protein_features"

    sequence_id: Mapped[uuid.UUID] = _SEQ_FK()
    gene: Mapped[str | None] = mapped_column(String(120), index=True)
    reviewed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, index=True
    )
    molecular_weight: Mapped[float | None] = mapped_column(Numeric(12, 2))
    function: Mapped[str | None] = mapped_column(Text)


class ProteinDomain(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "protein_domains"

    sequence_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("sequences.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    source: Mapped[str | None] = mapped_column(String(64))


class ProteinPdbRef(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "protein_pdb_refs"
    __table_args__ = (
        UniqueConstraint("sequence_id", "pdb_id", name="protein_pdb_refs_unique"),
    )

    sequence_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("sequences.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    pdb_id: Mapped[str] = mapped_column(String(16), nullable=False)


class CrisprFeature(Base):
    __tablename__ = "crispr_features"

    sequence_id: Mapped[uuid.UUID] = _SEQ_FK()
    cas_system: Mapped[CasSystem] = mapped_column(
        CAS_SYSTEM_ENUM, nullable=False, index=True
    )
    evidence_type: Mapped[CrisprEvidenceType] = mapped_column(
        CRISPR_EVIDENCE_TYPE_ENUM,
        nullable=False,
        index=True,
        default=CrisprEvidenceType.NATURAL_CRISPR_ELEMENT,
        server_default="natural_crispr_element",
    )
    target_gene: Mapped[str | None] = mapped_column(String(120), index=True)
    pam: Mapped[str | None] = mapped_column(String(16))
    genomic_target: Mapped[str | None] = mapped_column(String(120))
    on_target_score: Mapped[float | None] = mapped_column(Numeric(6, 4))
    off_target_score: Mapped[float | None] = mapped_column(Numeric(6, 4))
    target_source_accession: Mapped[str | None] = mapped_column(String(64), index=True)
    target_tax_id: Mapped[int | None] = mapped_column(Integer, index=True)
    source_pmid: Mapped[int | None] = mapped_column(Integer)
    method: Mapped[str | None] = mapped_column(String(80))


class VirusFeature(Base):
    __tablename__ = "virus_features"

    sequence_id: Mapped[uuid.UUID] = _SEQ_FK()
    family: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    host: Mapped[str | None] = mapped_column(String(300), index=True)
    genome_type: Mapped[GenomeType] = mapped_column(
        GENOME_TYPE_ENUM, nullable=False, index=True
    )
    segment: Mapped[str | None] = mapped_column(String(64))
