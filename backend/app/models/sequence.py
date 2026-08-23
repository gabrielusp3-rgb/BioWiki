from __future__ import annotations

import uuid

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.enums import MOLECULE_ENUM, SEQUENCE_TYPE_ENUM, Molecule, SequenceType
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Sequence(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "sequences"
    __table_args__ = (
        UniqueConstraint(
            "source_id", "accession", "version", name="sequences_source_accession_version"
        ),
        CheckConstraint("length >= 0", name="ck_sequences_length_non_negative"),
    )

    seq_type: Mapped[SequenceType] = mapped_column(SEQUENCE_TYPE_ENUM, nullable=False)
    molecule: Mapped[Molecule | None] = mapped_column(MOLECULE_ENUM)
    accession: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    version: Mapped[str | None] = mapped_column(String(16))
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    organism_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("organisms.id", ondelete="RESTRICT"),
        nullable=False,
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("data_sources.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    length: Mapped[int] = mapped_column(BigInteger, nullable=False)
    residues: Mapped[str | None] = mapped_column(Text)
    checksum: Mapped[str | None] = mapped_column(String(64), index=True)
    gc_content: Mapped[float | None] = mapped_column(Numeric(5, 4))
    source_updated_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    gene_name: Mapped[str | None] = mapped_column(String(120), index=True)
    gene_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("genes.id", ondelete="SET NULL"), index=True
    )
    chromosome: Mapped[str | None] = mapped_column(String(32))
    source_url: Mapped[str | None] = mapped_column(String(500))
    annotations: Mapped[dict | None] = mapped_column(JSONB)

    organism = relationship("Organism", lazy="selectin")
    source = relationship("DataSource", lazy="selectin")
    gene = relationship("Gene", lazy="selectin")

    dna_feature = relationship(
        "DnaFeature", uselist=False, lazy="selectin", cascade="all, delete-orphan"
    )
    rna_feature = relationship(
        "RnaFeature", uselist=False, lazy="selectin", cascade="all, delete-orphan"
    )
    protein_feature = relationship(
        "ProteinFeature", uselist=False, lazy="selectin", cascade="all, delete-orphan"
    )
    crispr_feature = relationship(
        "CrisprFeature", uselist=False, lazy="selectin", cascade="all, delete-orphan"
    )
    virus_feature = relationship(
        "VirusFeature", uselist=False, lazy="selectin", cascade="all, delete-orphan"
    )
    protein_domains = relationship(
        "ProteinDomain", lazy="selectin", cascade="all, delete-orphan"
    )
    pdb_refs = relationship(
        "ProteinPdbRef", lazy="selectin", cascade="all, delete-orphan"
    )
    cross_references = relationship(
        "SequenceCrossReference", lazy="selectin", cascade="all, delete-orphan"
    )
    references = relationship(
        "SequenceReference",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="SequenceReference.reference_order",
    )
