"""Checksum, accession identity and model-level deduplication keys."""

from __future__ import annotations

from app.models.publication import SequenceReference
from app.models.sequence import Sequence
from tests.fixtures import make_fixture_dna


def test_checksum_is_sha256_of_residues() -> None:
    ps = make_fixture_dna(residues="ATGC")
    digest = ps.checksum()
    assert digest is not None
    assert len(digest) == 64
    assert digest == make_fixture_dna(residues="ATGC").checksum()


def test_checksum_changes_when_residues_change() -> None:
    a = make_fixture_dna(residues="ATGC").checksum()
    b = make_fixture_dna(residues="ATGG").checksum()
    assert a != b


def test_checksum_absent_without_residues() -> None:
    ps = make_fixture_dna(residues=None, length=12)
    assert ps.checksum() is None


def test_same_accession_same_checksum_is_idempotent_identity() -> None:
    first = make_fixture_dna(accession="NM_000207", version="3", residues="ATGCATGC")
    second = make_fixture_dna(accession="NM_000207", version="3", residues="ATGCATGC")
    assert first.accession == second.accession
    assert first.version == second.version
    assert first.checksum() == second.checksum()
    assert first.source_key == second.source_key


def test_sequence_unique_constraint_covers_source_accession_version() -> None:
    names = {constraint.name for constraint in Sequence.__table__.constraints}
    assert "sequences_source_accession_version" in names


def test_sequence_reference_unique_pair() -> None:
    names = {constraint.name for constraint in SequenceReference.__table__.constraints}
    assert "uq_sequence_references_pair" in names
