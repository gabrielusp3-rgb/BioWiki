"""Distinguish natural CRISPR, experimental guides, and computational targets.

Revision ID: 0006_crispr_evidence
Revises: 0005_seed_categories
Create Date: 2026-08-29

Existing CRISPR rows are natural NCBI locus/array records and receive
``natural_crispr_element``. Computational scores stay NULL unless a real
implemented method wrote them.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006_crispr_evidence"
down_revision: Union[str, Sequence[str], None] = "0005_seed_categories"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_EVIDENCE_VALUES = (
    "natural_crispr_element",
    "experimental_guide",
    "computational_target",
)


def upgrade() -> None:
    bind = op.get_bind()
    op.execute(
        sa.text(
            """
            DO $$ BEGIN
                CREATE TYPE crispr_evidence_type AS ENUM (
                    'natural_crispr_element',
                    'experimental_guide',
                    'computational_target'
                );
            EXCEPTION
                WHEN duplicate_object THEN NULL;
            END $$;
            """
        )
    )
    evidence_enum = postgresql.ENUM(
        *_EVIDENCE_VALUES,
        name="crispr_evidence_type",
        create_type=False,
    )
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("crispr_features")}
    if "evidence_type" not in columns:
        op.add_column(
            "crispr_features",
            sa.Column(
                "evidence_type",
                evidence_enum,
                nullable=False,
                server_default="natural_crispr_element",
            ),
        )
        op.create_index(
            "ix_crispr_features_evidence_type",
            "crispr_features",
            ["evidence_type"],
        )
    if "target_source_accession" not in columns:
        op.add_column(
            "crispr_features",
            sa.Column("target_source_accession", sa.String(length=64), nullable=True),
        )
        op.create_index(
            "ix_crispr_features_target_source_accession",
            "crispr_features",
            ["target_source_accession"],
        )
    if "target_tax_id" not in columns:
        op.add_column(
            "crispr_features",
            sa.Column("target_tax_id", sa.Integer(), nullable=True),
        )
        op.create_index(
            "ix_crispr_features_target_tax_id",
            "crispr_features",
            ["target_tax_id"],
        )
    if "source_pmid" not in columns:
        op.add_column(
            "crispr_features",
            sa.Column("source_pmid", sa.Integer(), nullable=True),
        )
    if "method" not in columns:
        op.add_column(
            "crispr_features",
            sa.Column("method", sa.String(length=80), nullable=True),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("crispr_features")}
    indexes = {idx["name"] for idx in inspector.get_indexes("crispr_features")}
    if "ix_crispr_features_target_tax_id" in indexes:
        op.drop_index("ix_crispr_features_target_tax_id", table_name="crispr_features")
    if "ix_crispr_features_target_source_accession" in indexes:
        op.drop_index(
            "ix_crispr_features_target_source_accession", table_name="crispr_features"
        )
    if "ix_crispr_features_evidence_type" in indexes:
        op.drop_index("ix_crispr_features_evidence_type", table_name="crispr_features")
    for name in (
        "method",
        "source_pmid",
        "target_tax_id",
        "target_source_accession",
        "evidence_type",
    ):
        if name in columns:
            op.drop_column("crispr_features", name)
    op.execute(sa.text("DROP TYPE IF EXISTS crispr_evidence_type"))
