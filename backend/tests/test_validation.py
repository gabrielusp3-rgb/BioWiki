"""Unit tests for pipeline validation. Uses TEST FIXTURE objects only."""

from __future__ import annotations

import pytest

from app.pipeline.errors import ValidationError
from app.pipeline.models import ParsedOrganism
from app.pipeline.validation import (
    enrich,
    infer_group_from_lineage,
    pubmed_id_is_valid,
    source_taxonomy_is_unclassifiable,
    validate,
)
from tests.fixtures import make_fixture_dna, make_fixture_organism, make_fixture_protein


def test_valid_dna_fixture_passes() -> None:
    ps = make_fixture_dna()
    enrich(ps)
    validate(ps)


def test_empty_accession_rejected() -> None:
    ps = make_fixture_dna(accession="  ")
    with pytest.raises(ValidationError, match="accession"):
        validate(ps)


def test_empty_residues_and_length_rejected() -> None:
    ps = make_fixture_dna(residues="", length=0)
    enrich(ps)
    with pytest.raises(ValidationError, match="length"):
        validate(ps)


def test_missing_source_key_rejected() -> None:
    ps = make_fixture_dna(source_key="")
    with pytest.raises(ValidationError, match="source_key"):
        validate(ps)


def test_invalid_nucleotide_symbols_rejected() -> None:
    ps = make_fixture_dna(residues="ATGCXYZ")
    with pytest.raises(ValidationError, match="invalid symbols"):
        validate(ps)


def test_protein_requires_reviewed_flag() -> None:
    ps = make_fixture_protein(reviewed=None)
    with pytest.raises(ValidationError, match="reviewed"):
        validate(ps)


def test_lineage_infers_animal_from_metazoa() -> None:
    assert infer_group_from_lineage(["Eukaryota", "Metazoa", "Chordata"]) == "animal"


def test_lineage_does_not_invent_group_for_empty() -> None:
    assert infer_group_from_lineage([]) is None
    assert infer_group_from_lineage(None) is None


def test_pubmed_id_format() -> None:
    assert pubmed_id_is_valid(None) is True
    assert pubmed_id_is_valid(6318096) is True
    assert pubmed_id_is_valid(0) is False
    assert pubmed_id_is_valid(-12) is False


def test_synthetic_construct_is_unclassifiable() -> None:
    org = ParsedOrganism(
        scientific_name="synthetic construct",
        tax_id=32630,
        lineage=["other sequences", "artificial sequences"],
    )
    assert source_taxonomy_is_unclassifiable(org) is True


def test_patent_unclassified_skipped_without_inventing_group() -> None:
    ps = make_fixture_dna(
        accession="PI007675",
        seq_type="crispr",
        cas_system="other",
        organism=ParsedOrganism(
            scientific_name="unidentified",
            tax_id=32630,
            lineage=["unclassified sequences"],
            group=None,
        ),
    )
    enrich(ps)
    with pytest.raises(ValidationError, match="synthetic or unclassified"):
        validate(ps)


def test_classifiable_bacteria_lineage_is_not_rejected() -> None:
    org = make_fixture_organism(
        scientific_name="Escherichia coli",
        tax_id=562,
        lineage=["Bacteria", "Pseudomonadota", "Enterobacteriaceae"],
        group=None,
    )
    assert source_taxonomy_is_unclassifiable(org) is False
    ps = make_fixture_dna(organism=org)
    enrich(ps)
    validate(ps)
    assert ps.organism.group == "bacteria"
