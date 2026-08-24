"""Initial PostgreSQL schema for a clean BioWiki install.

Revision ID matches live databases already stamped at ``0004_publication_abstract``
before these files were committed. On those databases this revision is a no-op.
On an empty database it creates enums, tables, generated ``search_vector``,
and GIN indexes.

Revision ID: 0004_publication_abstract
Revises:
Create Date: 2026-08-23
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.database.base import Base
from app.models.enums import (
    AssemblyLevel,
    CasSystem,
    DnaMoleculeType,
    GenomeType,
    Molecule,
    OrganismGroup,
    RnaClass,
    SequenceType,
    Strand,
)
import app.models  # noqa: F401

revision: str = "0004_publication_abstract"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_ENUMS: tuple[tuple[str, type], ...] = (
    ("sequence_type", SequenceType),
    ("molecule", Molecule),
    ("dna_molecule_type", DnaMoleculeType),
    ("strand", Strand),
    ("rna_class", RnaClass),
    ("cas_system", CasSystem),
    ("genome_type", GenomeType),
    ("organism_group", OrganismGroup),
    ("assembly_level", AssemblyLevel),
)


def _create_enum(name: str, python_enum: type) -> None:
    values = ", ".join("'" + member.value.replace("'", "''") + "'" for member in python_enum)
    op.execute(sa.text(f"CREATE TYPE {name} AS ENUM ({values})"))


def upgrade() -> None:
    op.execute(sa.text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
    op.execute(sa.text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
    for name, python_enum in _ENUMS:
        _create_enum(name, python_enum)
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
    for name, _python_enum in reversed(_ENUMS):
        op.execute(sa.text(f"DROP TYPE IF EXISTS {name}"))
