"""CONTIG / missing-ORIGIN fallback for the NCBI fetcher.

Uses in-memory GenBank/FASTA fixtures and a fake EFetch client. No network,
no invented residues — the FASTA/gbwithparts bodies are the test's official
payloads, analogous to NCBI.
"""

from __future__ import annotations

from app.pipeline.fetchers.ncbi import (
    fetch_records,
    parse_fasta_residues,
    try_attach_official_residues,
)
from app.pipeline.models import ParsedSequence
from tests.fixtures import make_fixture_dna

_CONTIG_GB = """\
LOCUS       NG_TEST001               12 bp    DNA     linear   CON 05-AUG-2026
DEFINITION  Test antimicrobial-resistance contig CDS.
ACCESSION   NG_TEST001
VERSION     NG_TEST001.1
KEYWORDS    RefSeq.
SOURCE      Escherichia coli
  ORGANISM  Escherichia coli
            Bacteria; Pseudomonadota; Gammaproteobacteria; Enterobacterales.
FEATURES             Location/Qualifiers
     source          1..12
                     /organism="Escherichia coli"
                     /mol_type="genomic DNA"
                     /db_xref="taxon:562"
     gene            1..12
                     /gene="blaTEM"
CONTIG      join(XX000001.1:1..12)
"""

_FASTA_MATCH = """\
>NG_TEST001.1 Test antimicrobial-resistance contig CDS
ATGCATGCATGC
"""

_FASTA_MISMATCH = """\
>NG_TEST001.1 Test antimicrobial-resistance contig CDS
ATGCATGCA
"""

_GBWITHPARTS = """\
LOCUS       NG_TEST001               12 bp    DNA     linear   CON 05-AUG-2026
DEFINITION  Test antimicrobial-resistance contig CDS.
ACCESSION   NG_TEST001
VERSION     NG_TEST001.1
KEYWORDS    RefSeq.
SOURCE      Escherichia coli
  ORGANISM  Escherichia coli
            Bacteria; Pseudomonadota; Gammaproteobacteria; Enterobacterales.
FEATURES             Location/Qualifiers
     source          1..12
                     /organism="Escherichia coli"
                     /mol_type="genomic DNA"
                     /db_xref="taxon:562"
ORIGIN
        1 atgcatgcat gc
//
"""


class FakeNCBI:
    """Minimal stand-in for NCBIConnector.efetch."""

    def __init__(self, *, gb: str = "", fasta: str = "", gbwithparts: str = "") -> None:
        self.gb = gb
        self.fasta = fasta
        self.gbwithparts = gbwithparts
        self.rettypes: list[str] = []

    async def efetch(self, db, ids, *, rettype: str = "fasta", retmode: str = "text") -> str:
        self.rettypes.append(rettype)
        if rettype in {"gb", "gp"}:
            return self.gb
        if rettype == "fasta":
            return self.fasta
        if rettype == "gbwithparts":
            return self.gbwithparts
        return ""

    async def aclose(self) -> None:
        return None


def test_parse_fasta_residues_plain_and_ref_header() -> None:
    plain = parse_fasta_residues(_FASTA_MATCH)
    assert plain["NG_TEST001"] == "ATGCATGCATGC"
    assert plain["NG_TEST001.1"] == "ATGCATGCATGC"
    ref = parse_fasta_residues(
        ">ref|NG_TEST001.1| Test\nATGCATGCATGC\n"
    )
    assert ref["NG_TEST001"] == "ATGCATGCATGC"


def test_attach_refuses_length_mismatch() -> None:
    ps = make_fixture_dna(accession="NG_TEST001", residues=None, length=12)
    assert ps.residues is None
    ok = try_attach_official_residues(ps, "ATGCATGCA", source_label="FASTA")
    assert ok is False
    assert ps.residues is None


def test_attach_accepts_matching_official_sequence() -> None:
    ps = make_fixture_dna(accession="NG_TEST001", residues=None, length=12)
    ok = try_attach_official_residues(ps, "atgcatgcatgc", source_label="FASTA")
    assert ok is True
    assert ps.residues == "ATGCATGCATGC"


async def test_fetch_records_fills_contig_via_fasta() -> None:
    fake = FakeNCBI(gb=_CONTIG_GB, fasta=_FASTA_MATCH)
    records = await fetch_records(
        ["NG_TEST001"],
        db="nuccore",
        seq_type="dna",
        connector=fake,  # type: ignore[arg-type]
    )
    assert len(records) == 1
    rec = records[0]
    assert rec.accession == "NG_TEST001"
    assert rec.residues == "ATGCATGCATGC"
    assert rec.length == 12
    assert rec.annotations and rec.annotations.get("CONTIG") == "join(XX000001.1:1..12)"
    assert "gb" in fake.rettypes
    assert "fasta" in fake.rettypes


async def test_fetch_records_does_not_force_mismatched_fasta() -> None:
    fake = FakeNCBI(gb=_CONTIG_GB, fasta=_FASTA_MISMATCH)
    records = await fetch_records(
        ["NG_TEST001"],
        db="nuccore",
        seq_type="dna",
        connector=fake,  # type: ignore[arg-type]
    )
    assert len(records) == 1
    assert records[0].residues is None
    assert records[0].length == 12


async def test_fetch_records_gbwithparts_when_fasta_empty() -> None:
    fake = FakeNCBI(gb=_CONTIG_GB, fasta="", gbwithparts=_GBWITHPARTS)
    records = await fetch_records(
        ["NG_TEST001"],
        db="nuccore",
        seq_type="dna",
        connector=fake,  # type: ignore[arg-type]
    )
    assert len(records) == 1
    assert records[0].residues == "ATGCATGCATGC"
    assert "gbwithparts" in fake.rettypes


def test_parsed_sequence_checksum_from_attached_residues() -> None:
    ps = ParsedSequence(
        seq_type="dna",
        accession="NG_TEST001",
        name="test",
        organism=make_fixture_dna().organism,
        source_key="ncbi_refseq",
        residues=None,
        length=12,
    )
    assert ps.checksum() is None
    assert try_attach_official_residues(ps, "ATGCATGCATGC", source_label="FASTA")
    digest = ps.checksum()
    assert digest is not None and len(digest) == 64
