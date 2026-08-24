from __future__ import annotations

import uuid

from sqlalchemy import BigInteger, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Gene(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "genes"
    __table_args__ = (
        UniqueConstraint("organism_id", "symbol", name="uq_genes_organism_symbol"),
    )

    symbol: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    name: Mapped[str | None] = mapped_column(String(300))
    description: Mapped[str | None] = mapped_column(Text)
    organism_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("organisms.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    entrez_gene_id: Mapped[int | None] = mapped_column(BigInteger, unique=True)
    ensembl_gene_id: Mapped[str | None] = mapped_column(String(64))
    chromosome: Mapped[str | None] = mapped_column(String(32))
    map_location: Mapped[str | None] = mapped_column(String(64))

    organism = relationship("Organism", lazy="selectin")
