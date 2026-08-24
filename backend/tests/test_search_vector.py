"""Read-only checks that the live schema matches the search-critical objects."""

from __future__ import annotations

from sqlalchemy import text
import pytest

from app.database.session import get_sessionmaker
from app.models.sequence import Sequence


async def test_search_vector_is_stored_generated_column() -> None:
    async with get_sessionmaker()() as session:
        row = (
            await session.execute(
                text(
                    """
                    SELECT is_generated, generation_expression
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = 'sequences'
                      AND column_name = 'search_vector'
                    """
                )
            )
        ).one()
    assert row.is_generated == "ALWAYS"
    expr = (row.generation_expression or "").lower()
    assert "to_tsvector" in expr
    assert "english" in expr
    assert "name" in expr
    assert "accession" in expr
    assert "gene_name" in expr
    assert "description" in expr


async def test_search_vector_gin_and_trigram_indexes_exist() -> None:
    async with get_sessionmaker()() as session:
        names = set(
            (
                await session.execute(
                    text(
                        """
                        SELECT indexname FROM pg_indexes
                        WHERE schemaname = 'public' AND tablename = 'sequences'
                        """
                    )
                )
            ).scalars()
        )
    assert "ix_sequences_search_vector" in names
    assert "ix_sequences_name_trgm" in names
    assert "ix_sequences_organism_type" in names
    assert "ix_sequences_type_length" in names


async def test_publication_trigram_indexes_exist() -> None:
    async with get_sessionmaker()() as session:
        names = set(
            (
                await session.execute(
                    text(
                        """
                        SELECT indexname FROM pg_indexes
                        WHERE schemaname = 'public' AND tablename = 'publications'
                        """
                    )
                )
            ).scalars()
        )
    assert "ix_publications_title_trgm" in names
    assert "ix_publications_abstract_trgm" in names


async def test_orm_declares_search_vector_as_computed() -> None:
    col = Sequence.__table__.c.search_vector
    assert col.computed is not None
    assert col.computed.persisted is True


@pytest.mark.live
async def test_live_fts_matches_existing_insulin_records() -> None:
    async with get_sessionmaker()() as session:
        hits = (
            await session.execute(
                text(
                    """
                    SELECT accession FROM sequences
                    WHERE search_vector @@ websearch_to_tsquery('english', :q)
                    LIMIT 5
                    """
                ),
                {"q": "insulin"},
            )
        ).scalars().all()
    assert hits


async def test_required_extensions_installed() -> None:
    async with get_sessionmaker()() as session:
        ext = set(
            (
                await session.execute(text("SELECT extname FROM pg_extension"))
            ).scalars()
        )
    assert "pg_trgm" in ext
    assert "pgcrypto" in ext or "plpgsql" in ext


async def test_live_alembic_revision_matches_repo() -> None:
    async with get_sessionmaker()() as session:
        stamped = (
            await session.execute(text("SELECT version_num FROM alembic_version"))
        ).scalar_one()
    assert stamped == "0004_publication_abstract"
