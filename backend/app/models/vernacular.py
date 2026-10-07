"""Locale-specific vernacular names for one organism. Not a second species row."""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class OrganismVernacularName(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "organism_vernacular_names"
    __table_args__ = (
        UniqueConstraint("organism_id", "locale", name="uq_organism_vernacular_locale"),
    )

    organism_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("organisms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    locale: Mapped[str] = mapped_column(String(16), nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    source: Mapped[str] = mapped_column(String(80), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(500))
    verification_status: Mapped[str] = mapped_column(String(40), nullable=False)
