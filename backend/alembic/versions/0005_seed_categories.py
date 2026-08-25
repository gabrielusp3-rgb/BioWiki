"""Seed UI category rows so homepage counts are never missing.

Revision ID: 0005_seed_categories
Revises: 0004_publication_abstract
Create Date: 2026-08-24
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005_seed_categories"
down_revision: Union[str, Sequence[str], None] = "0004_publication_abstract"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            INSERT INTO categories (key, label, sequence_count) VALUES
              ('dna', 'DNA', 0),
              ('rna', 'RNA', 0),
              ('protein', 'Protein', 0),
              ('crispr', 'CRISPR', 0),
              ('virus', 'Virus', 0),
              ('genome', 'Genome', 0)
            ON CONFLICT (key) DO NOTHING
            """
        )
    )


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM categories WHERE key IN ('dna','rna','protein','crispr','virus','genome')"))
