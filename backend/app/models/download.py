from __future__ import annotations

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Download(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "downloads"
    __table_args__ = (
        CheckConstraint(
            "format IN ('fasta','json','csv','genbank')",
            name="ck_downloads_format",
        ),
    )

    slug: Mapped[str] = mapped_column(String(160), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    category_key: Mapped[str | None] = mapped_column(
        ForeignKey("categories.key", ondelete="SET NULL"), index=True
    )
    format: Mapped[str] = mapped_column(String(16), nullable=False)
    file_path: Mapped[str | None] = mapped_column(String(500))
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    record_count: Mapped[int | None] = mapped_column(BigInteger)
    checksum: Mapped[str | None] = mapped_column(String(64))
    generated_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))
