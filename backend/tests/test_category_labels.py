from app.services.sync_service import CATEGORY_LABELS, CATEGORY_TYPES


def test_every_ui_category_has_a_label() -> None:
    assert set(CATEGORY_TYPES) == set(CATEGORY_LABELS)
    assert set(CATEGORY_TYPES) == {"dna", "rna", "protein", "crispr", "virus", "genome"}
