from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.mixins import TimestampMixin


class Taxonomy(TimestampMixin, Base):
    __tablename__ = "taxonomy"

    tax_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    scientific_name: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    common_name: Mapped[str | None] = mapped_column(String(300))
    rank: Mapped[str | None] = mapped_column(String(64), index=True)
    division: Mapped[str | None] = mapped_column(String(64))
    parent_tax_id: Mapped[int | None] = mapped_column(
        ForeignKey("taxonomy.tax_id", ondelete="SET NULL"), index=True
    )
