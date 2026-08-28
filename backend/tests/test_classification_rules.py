"""Classification rules: semantic category, molecule, and source LOCUS."""

from __future__ import annotations

import pytest

from app.pipeline.errors import ValidationError
from app.pipeline.models import ImportContext, ParsedOrganism
from app.pipeline.parsers.genbank import GenBankParser
from app.pipeline.taxonomy import group_from_taxonomy, parse_ncbi_taxonomy_xml
from app.pipeline.validation import enrich, validate
from tests.fixtures import (
    make_fixture_crispr,
    make_fixture_dna,
    make_fixture_protein,
    make_fixture_rna,
    make_fixture_virus,
)

_MRNA_GB = """\
LOCUS       NM_TEST001              12 bp    mRNA    linear   VRT 05-AUG-2026
DEFINITION  TEST FIXTURE insulin mRNA.
ACCESSION   NM_TEST001
VERSION     NM_TEST001.1
SOURCE      Homo sapiens
  ORGANISM  Homo sapiens
            Eukaryota; Metazoa; Chordata; Mammalia; Primates; Hominidae; Homo.
FEATURES             Location/Qualifiers
     source          1..12
                     /organism="Homo sapiens"
                     /mol_type="mRNA"
                     /db_xref="taxon:9606"
ORIGIN
        1 atgcatgcat gc
//
"""

_VIRUS_RNA_GB = """\
LOCUS       NC_TESTV                 12 bp    RNA     linear   VRL 05-AUG-2026
DEFINITION  TEST FIXTURE viral RNA.
ACCESSION   NC_TESTV
VERSION     NC_TESTV.1
SOURCE      Influenza A virus
  ORGANISM  Influenza A virus
            Viruses; Riboviria; Orthomyxoviridae.
FEATURES             Location/Qualifiers
     source          1..12
                     /organism="Influenza A virus"
                     /mol_type="viral RNA"
                     /db_xref="taxon:11320"
ORIGIN
        1 atgcatgcat gc
//
"""

_CRISPR_DNA_GB = """\
LOCUS       CP_TESTCR                60 bp    DNA     linear   BCT 05-AUG-2026
DEFINITION  Streptococcus pyogenes CRISPR-Cas9 associated array.
ACCESSION   CP_TESTCR
VERSION     CP_TESTCR.1
SOURCE      Streptococcus pyogenes
  ORGANISM  Streptococcus pyogenes
            Bacteria; Bacillota; Bacilli; Lactobacillales; Streptococcaceae.
FEATURES             Location/Qualifiers
     source          1..60
                     /organism="Streptococcus pyogenes"
                     /mol_type="genomic DNA"
                     /db_xref="taxon:1314"
ORIGIN
        1 gttttagagc tagaaatagc aagttaaaat aaggctagtc cgttatcaac ttgaaaaagt
//
"""

_TAXONOMY_XML = """\
<TaxaSet>
  <Taxon>
    <TaxId>9755</TaxId>
    <ScientificName>Physeter macrocephalus</ScientificName>
    <Division>Mammals</Division>
    <Lineage>cellular organisms; Eukaryota; Metazoa; Chordata; Mammalia; Physeteridae; Physeter</Lineage>
  </Taxon>
  <Taxon>
    <TaxId>3721</TaxId>
    <ScientificName>Crambe hispanica subsp. abyssinica</ScientificName>
    <Division>Plants and Fungi</Division>
    <Lineage>cellular organisms; Eukaryota; Viridiplantae; Streptophyta; Brassicaceae; Crambe</Lineage>
  </Taxon>
</TaxaSet>
"""


def test_protein_cannot_enter_as_dna() -> None:
    ps = make_fixture_protein(seq_type="dna", molecule="dna", molecule_type="gene")
    with pytest.raises(ValidationError, match="invalid symbols"):
        validate(ps)


def test_protein_cannot_enter_as_rna() -> None:
    ps = make_fixture_protein(seq_type="rna", molecule="rna", rna_class="mrna")
    with pytest.raises(ValidationError, match="invalid symbols"):
        validate(ps)


def test_long_nucleotide_string_rejected_as_protein() -> None:
    ps = make_fixture_protein(residues="ATGC" * 30)
    with pytest.raises(ValidationError, match="nucleotide alphabet"):
        validate(ps)


def test_protein_requires_protein_molecule() -> None:
    ps = make_fixture_protein(molecule="dna")
    with pytest.raises(ValidationError, match="incompatible"):
        validate(ps)


def test_rna_ncbi_t_residues_are_not_reclassified_as_dna() -> None:
    ps = make_fixture_rna(residues="ATGCTTTTAAAA")
    enrich(ps)
    validate(ps)
    assert ps.seq_type == "rna"
    assert ps.molecule == "rna"
    assert "T" in ps.residues


def test_virus_may_have_dna_molecule() -> None:
    ps = make_fixture_virus(molecule="dna", genome_type="dsDNA")
    enrich(ps)
    validate(ps)
    assert ps.seq_type == "virus"
    assert ps.molecule == "dna"


def test_virus_may_have_rna_molecule() -> None:
    ps = make_fixture_virus(molecule="rna")
    enrich(ps)
    validate(ps)
    assert ps.seq_type == "virus"
    assert ps.molecule == "rna"


def test_crispr_is_not_converted_to_dna_by_alphabet() -> None:
    ps = make_fixture_crispr()
    enrich(ps)
    validate(ps)
    assert ps.seq_type == "crispr"
    assert ps.molecule == "dna"


def test_genbank_mrna_not_stored_as_dna_when_context_says_dna() -> None:
    parser = GenBankParser()
    context = ImportContext(source_key="ncbi_refseq", seq_type="dna", molecule="dna")
    records = list(parser.parse(_MRNA_GB, context))
    assert len(records) == 1
    assert records[0].seq_type == "rna"
    assert records[0].molecule == "rna"
    assert records[0].rna_class == "mrna"


def test_genbank_virus_context_keeps_virus_with_rna_molecule() -> None:
    parser = GenBankParser()
    context = ImportContext(source_key="ncbi_refseq", seq_type="virus")
    records = list(parser.parse(_VIRUS_RNA_GB, context))
    assert len(records) == 1
    assert records[0].seq_type == "virus"
    assert records[0].molecule == "rna"


def test_genbank_crispr_context_is_not_rewritten_to_dna() -> None:
    parser = GenBankParser()
    context = ImportContext(source_key="ncbi_genbank", seq_type="crispr", cas_system="cas9")
    records = list(parser.parse(_CRISPR_DNA_GB, context))
    assert len(records) == 1
    assert records[0].seq_type == "crispr"
    assert records[0].molecule == "dna"
    assert records[0].cas_system == "cas9"


def test_plants_and_fungi_division_is_not_bacteria() -> None:
    assert group_from_taxonomy(lineage=[], division="Plants and Fungi") is None
    assert (
        group_from_taxonomy(
            lineage=["Eukaryota", "Viridiplantae", "Brassicaceae"],
            division="Plants and Fungi",
        )
        == "plant"
    )


def test_taxonomy_xml_lineage_classifies_whale_as_animal() -> None:
    parsed = parse_ncbi_taxonomy_xml(_TAXONOMY_XML)
    whale = parsed[9755]
    assert group_from_taxonomy(lineage=whale["lineage"], division=whale["division"]) == "animal"
    plant = parsed[3721]
    assert group_from_taxonomy(lineage=plant["lineage"], division=plant["division"]) == "plant"


def test_organism_without_group_or_lineage_is_rejected() -> None:
    ps = make_fixture_dna(
        organism=ParsedOrganism(
            scientific_name="unknown organism",
            tax_id=999999,
            lineage=[],
            group=None,
        )
    )
    enrich(ps)
    with pytest.raises(ValidationError, match="refusing to invent a kingdom"):
        validate(ps)


def test_dna_fixture_still_passes() -> None:
    ps = make_fixture_dna()
    enrich(ps)
    validate(ps)
