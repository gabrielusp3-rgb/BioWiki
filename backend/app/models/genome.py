from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.enums import ASSEMBLY_LEVEL_ENUM, AssemblyLevel
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class GenomeRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "genome_records"
    __table_args__ = (
        CheckConstraint(
            "total_length IS NULL OR total_length >= 0",
            name="ck_genome_records_total_length_non_negative",
        ),
    )

    accession: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    assembly_name: Mapped[str | None] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    organism_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("organisms.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("data_sources.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    assembly_level: Mapped[AssemblyLevel] = mapped_column(
        ASSEMBLY_LEVEL_ENUM, nullable=False, index=True
    )
    total_length: Mapped[int | None] = mapped_column(BigInteger)
    chromosome_count: Mapped[int | None] = mapped_column(Integer)
    scaffold_count: Mapped[int | None] = mapped_column(Integer)
    contig_count: Mapped[int | None] = mapped_column(Integer)
    gc_content: Mapped[float | None] = mapped_column(Numeric(5, 4))
    release_date: Mapped[date | None] = mapped_column(Date)
    source_url: Mapped[str | None] = mapped_column(String(500))
    source_updated_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    annotations: Mapped[dict | None] = mapped_column(JSONB)

    organism = relationship("Organism", lazy="selectin")
    source = relationship("DataSource", lazy="selectin")
