from __future__ import annotations

import uuid

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Publication(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "publications"
    __table_args__ = (
        CheckConstraint(
            "year IS NULL OR (year >= 1800 AND year <= 2100)",
            name="ck_publications_year_range",
        ),
    )

    pubmed_id: Mapped[int | None] = mapped_column(BigInteger, unique=True)
    doi: Mapped[str | None] = mapped_column(String(255), unique=True)
    pmc_id: Mapped[str | None] = mapped_column(String(32))
    title: Mapped[str] = mapped_column(Text, nullable=False)
    abstract: Mapped[str | None] = mapped_column(Text)
    authors: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    journal: Mapped[str | None] = mapped_column(String(300))
    year: Mapped[int | None] = mapped_column(Integer, index=True)
    volume: Mapped[str | None] = mapped_column(String(32))
    pages: Mapped[str | None] = mapped_column(String(64))
    url: Mapped[str | None] = mapped_column(String(500))


class SequenceReference(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "sequence_references"
    __table_args__ = (
        UniqueConstraint(
            "sequence_id", "publication_id", name="uq_sequence_references_pair"
        ),
    )

    sequence_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("sequences.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    publication_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("publications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reference_order: Mapped[int | None] = mapped_column(Integer)

    publication = relationship("Publication", lazy="selectin")
