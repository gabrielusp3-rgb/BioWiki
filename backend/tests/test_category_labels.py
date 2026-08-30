from app.services.sync_service import CATEGORY_LABELS, CATEGORY_TYPES
from tests.alembic_head import repo_alembic_head


def test_every_ui_category_has_a_label() -> None:
    assert set(CATEGORY_TYPES) == set(CATEGORY_LABELS)
    assert set(CATEGORY_TYPES) == {"dna", "rna", "protein", "crispr", "virus", "genome"}


def test_alembic_head_is_paleogenomics() -> None:
    assert repo_alembic_head() == "0007_paleogenomics"
