"""TEST FIXTURE builders.

These objects exist only in memory for unit tests. They are labelled TEST
FIXTURE in names and docstrings and must never be inserted into the
production BIOWIKI database.
"""

from __future__ import annotations

from app.pipeline.models import ParsedOrganism, ParsedSequence


def make_fixture_organism(**overrides) -> ParsedOrganism:
    """TEST FIXTURE: in-memory organism. Do not persist."""
    data = dict(
        scientific_name="TEST FIXTURE organism",
        tax_id=9606,
        lineage=["Eukaryota", "Metazoa", "Chordata"],
        group="animal",
    )
    data.update(overrides)
    return ParsedOrganism(**data)


def make_fixture_dna(**overrides) -> ParsedSequence:
    """TEST FIXTURE: in-memory DNA record. Do not persist."""
    data = dict(
        seq_type="dna",
        accession="TEST_FIXTURE_DNA",
        name="TEST FIXTURE DNA record",
        organism=make_fixture_organism(),
        source_key="ncbi_refseq",
        source_name="TEST FIXTURE source",
        molecule="dna",
        molecule_type="gene",
        residues="ATGCATGCATGC",
        length=12,
    )
    data.update(overrides)
    return ParsedSequence(**data)


def make_fixture_protein(**overrides) -> ParsedSequence:
    """TEST FIXTURE: in-memory protein record. Do not persist."""
    data = dict(
        seq_type="protein",
        accession="TEST_FIXTURE_PROT",
        name="TEST FIXTURE protein record",
        organism=make_fixture_organism(),
        source_key="uniprot",
        molecule="protein",
        residues="MKTFF",
        reviewed=True,
    )
    data.update(overrides)
    return ParsedSequence(**data)


def make_fixture_rna(**overrides) -> ParsedSequence:
    """TEST FIXTURE: in-memory RNA record. Do not persist."""
    data = dict(
        seq_type="rna",
        accession="TEST_FIXTURE_RNA",
        name="TEST FIXTURE RNA transcript",
        organism=make_fixture_organism(),
        source_key="ncbi_refseq",
        molecule="rna",
        rna_class="mrna",
        residues="ATGCATGCATGC",
        length=12,
        is_coding=True,
    )
    data.update(overrides)
    return ParsedSequence(**data)


def make_fixture_virus(**overrides) -> ParsedSequence:
    """TEST FIXTURE: in-memory virus record. Do not persist."""
    data = dict(
        seq_type="virus",
        accession="TEST_FIXTURE_VIRUS",
        name="TEST FIXTURE virus record",
        organism=make_fixture_organism(
            scientific_name="TEST FIXTURE virus",
            tax_id=11320,
            lineage=["Viruses", "Orthomyxoviridae"],
            group="virus",
        ),
        source_key="ncbi_refseq",
        molecule="rna",
        family="Orthomyxoviridae",
        genome_type="ssRNA-",
        residues="ATGCATGCATGC",
        length=12,
    )
    data.update(overrides)
    return ParsedSequence(**data)


def make_fixture_crispr(**overrides) -> ParsedSequence:
    """TEST FIXTURE: in-memory CRISPR record. Do not persist."""
    data = dict(
        seq_type="crispr",
        accession="TEST_FIXTURE_CRISPR",
        name="TEST FIXTURE CRISPR guide",
        organism=make_fixture_organism(
            scientific_name="TEST FIXTURE streptococcus",
            tax_id=1303,
            lineage=["Bacteria", "Bacillota", "Streptococcaceae"],
            group="bacteria",
        ),
        source_key="ncbi_genbank",
        molecule="dna",
        cas_system="cas9",
        residues="GTTTTAGAGCTAGAAATAGCAAGTTAAAATAAGGCTAGTCCGTTATCAACTTGAAAAAGT",
        length=60,
        pam="NGG",
        target_gene="TEST",
    )
    data.update(overrides)
    return ParsedSequence(**data)
