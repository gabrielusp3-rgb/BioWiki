"""Add organism vernacular names. Does not copy or delete catalogue rows.

Revision ID: 0008_organism_vernacular
Revises: 0007_paleogenomics
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0008_organism_vernacular"
down_revision: Union[str, Sequence[str], None] = "0007_paleogenomics"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "organism_vernacular_names" in inspector.get_table_names():
        return
    op.create_table(
        "organism_vernacular_names",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("organism_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organisms.id", ondelete="CASCADE"), nullable=False),
        sa.Column("locale", sa.String(length=16), nullable=False),
        sa.Column("name", sa.String(length=300), nullable=False),
        sa.Column("source", sa.String(length=80), nullable=False),
        sa.Column("source_url", sa.String(length=500), nullable=True),
        sa.Column("verification_status", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("organism_id", "locale", name="uq_organism_vernacular_locale"),
    )
    op.create_index("ix_organism_vernacular_names_organism_id", "organism_vernacular_names", ["organism_id"])


def downgrade() -> None:
    op.drop_index("ix_organism_vernacular_names_organism_id", table_name="organism_vernacular_names")
    op.drop_table("organism_vernacular_names")
