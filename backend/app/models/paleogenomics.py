"""Paleogenomics collection: membership and curated profiles, not a molecule type."""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class PaleogenomicProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "paleogenomic_profiles"

    organism_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("organisms.id", ondelete="RESTRICT"),
        unique=True,
        nullable=False,
    )
    slug: Mapped[str] = mapped_column(String(160), unique=True, nullable=False, index=True)
    common_name: Mapped[str] = mapped_column(String(160), nullable=False)
    geographic_region: Mapped[str | None] = mapped_column(String(160))
    subsection: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    featured_rank: Mapped[int | None] = mapped_column(Integer)
    deextinction_status: Mapped[str] = mapped_column(String(64), nullable=False, default="unknown")
    last_reviewed_on: Mapped[date | None] = mapped_column(Date)
    taxonomic_uncertainty: Mapped[str | None] = mapped_column(Text)
    paleogenomic_data_available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    organism = relationship("Organism", lazy="selectin")
    claims = relationship(
        "PaleogenomicClaim",
        back_populates="profile",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="PaleogenomicClaim.sort_order",
    )


class PaleogenomicClaim(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "paleogenomic_claims"
    __table_args__ = (
        UniqueConstraint("profile_id", "section_key", name="uq_paleogenomic_claims_section"),
    )

    profile_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("paleogenomic_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    section_key: Mapped[str] = mapped_column(String(40), nullable=False)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_level: Mapped[str] = mapped_column(String(32), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_reviewed_on: Mapped[date | None] = mapped_column(Date)

    profile = relationship("PaleogenomicProfile", back_populates="claims")
    sources = relationship(
        "PaleogenomicClaimSource",
        back_populates="claim",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class PaleogenomicClaimSource(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "paleogenomic_claim_sources"

    claim_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("paleogenomic_claims.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    publication_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("publications.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    pubmed_id: Mapped[int | None] = mapped_column(BigInteger)
    doi: Mapped[str | None] = mapped_column(String(255))
    url: Mapped[str | None] = mapped_column(String(500))
    label: Mapped[str | None] = mapped_column(String(300))

    claim = relationship("PaleogenomicClaim", back_populates="sources")
    publication = relationship("Publication", lazy="selectin")


class PaleogenomicSequenceMembership(UUIDPrimaryKeyMixin, Base):
    """Marks an existing Sequence as part of the paleogenomics collection."""

    __tablename__ = "paleogenomic_sequence_membership"
    __table_args__ = (
        UniqueConstraint("sequence_id", name="uq_paleogenomic_sequence_membership_sequence"),
    )

    sequence_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("sequences.id", ondelete="CASCADE"),
        nullable=False,
    )
    profile_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("paleogenomic_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    record_kind: Mapped[str] = mapped_column(String(32), nullable=False, default="other")
    is_complete_mitogenome: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    specimen_label: Mapped[str | None] = mapped_column(String(160))
    biosample: Mapped[str | None] = mapped_column(String(64), index=True)
    bioproject: Mapped[str | None] = mapped_column(String(64), index=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    sequence = relationship("Sequence", lazy="noload")
    profile = relationship("PaleogenomicProfile", lazy="noload")


class PaleogenomicProject(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Public BioProject/BioSample/SRA metadata. Not raw reads."""

    __tablename__ = "paleogenomic_projects"
    __table_args__ = (
        UniqueConstraint(
            "bioproject",
            "biosample",
            "run_accession",
            name="uq_paleogenomic_projects_accessions",
        ),
    )

    profile_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("paleogenomic_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    bioproject: Mapped[str | None] = mapped_column(String(64), index=True)
    biosample: Mapped[str | None] = mapped_column(String(64), index=True)
    run_accession: Mapped[str | None] = mapped_column(String(64))
    experiment_accession: Mapped[str | None] = mapped_column(String(64))
    library_strategy: Mapped[str | None] = mapped_column(String(80))
    source_url: Mapped[str | None] = mapped_column(String(500))
    notes: Mapped[str | None] = mapped_column(Text)
    controlled_access: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class PaleogenomicIntrogressionRegion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Archaic ancestry in living Homo sapiens. Not ancient specimen DNA."""

    __tablename__ = "paleogenomic_introgression_regions"
    __table_args__ = (
        UniqueConstraint(
            "archaic_source",
            "gene_name",
            "reference_build",
            "chromosome",
            "start_position",
            "end_position",
            name="uq_paleogenomic_introgression_interval",
        ),
    )

    modern_organism_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("organisms.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    archaic_source: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    gene_name: Mapped[str | None] = mapped_column(String(80), index=True)
    locus_name: Mapped[str | None] = mapped_column(String(160))
    reference_build: Mapped[str | None] = mapped_column(String(32))
    chromosome: Mapped[str | None] = mapped_column(String(16))
    start_position: Mapped[int | None] = mapped_column(Integer)
    end_position: Mapped[int | None] = mapped_column(Integer)
    publication_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("publications.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    pubmed_id: Mapped[int | None] = mapped_column(BigInteger)
    doi: Mapped[str | None] = mapped_column(String(255))
    method: Mapped[str | None] = mapped_column(String(160))
    evidence_notes: Mapped[str] = mapped_column(Text, nullable=False)
    source_dataset: Mapped[str | None] = mapped_column(String(160))

    modern_organism = relationship("Organism", lazy="selectin")
    publication = relationship("Publication", lazy="selectin")


class PaleogenomicPublicationMembership(UUIDPrimaryKeyMixin, Base):
    """Links a Publication to a species profile without duplicating the article."""

    __tablename__ = "paleogenomic_publication_membership"
    __table_args__ = (
        UniqueConstraint(
            "profile_id",
            "publication_id",
            name="uq_paleogenomic_publication_membership",
        ),
    )

    profile_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("paleogenomic_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    publication_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("publications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
