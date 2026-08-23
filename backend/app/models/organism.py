from __future__ import annotations

from sqlalchemy import BigInteger, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.enums import ORGANISM_GROUP_ENUM, OrganismGroup
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Organism(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "organisms"

    slug: Mapped[str] = mapped_column(String(160), unique=True, nullable=False)
    scientific_name: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    common_name: Mapped[str | None] = mapped_column(String(300))
    tax_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    rank: Mapped[str | None] = mapped_column(String(64))
    lineage: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    group: Mapped[OrganismGroup] = mapped_column(
        "group", ORGANISM_GROUP_ENUM, nullable=False, index=True
    )
    image_url: Mapped[str | None] = mapped_column(String(500))
    sequence_count: Mapped[int | None] = mapped_column(BigInteger)
