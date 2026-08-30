"""Paleogenomics scientific semantics. No database required."""

from __future__ import annotations

from app.models.enums import EvidenceLevel, SequenceType
from app.pipeline.paleogenomics.catalogue import SPECIES, species_by_tax_id
from app.pipeline.paleogenomics.citations import (
    SHAPIRO_2002_FLIGHT_OF_THE_DODO,
    SANKARARAMAN_2014_NEANDERTHAL_ANCESTRY,
)
from app.pipeline.paleogenomics.introgression import INTROGRESSION_LOCI, introgression_modern_tax_id
from app.pipeline.paleogenomics.narratives import NARRATIVES
from app.pipeline.paleogenomics.semantics import (
    introgression_is_not_ancient_specimen,
    is_complete_mitogenome,
    living_relative_is_not_extinct,
    normalize_doi,
    sequence_length_allowed_for_catalogue,
    sra_run_is_not_a_sequence_accession,
)

LOCKED_TAX_IDS = {
    "homo-neanderthalensis": 63221,
    "homo-denisova": 741158,
    "thylacinus-cynocephalus": 9275,
    "coelodonta-antiquitatis": 222863,
    "raphus-cucullatus": 187135,
    "mammuthus-primigenius": 37349,
    "mammut-americanum": 39053,
    "smilodon-populator": 339609,
    "bos-primigenius": 9909,
    "equus-quagga-quagga": 555873,
    "ectopistes-migratorius": 187118,
    "hydrodamalis-gigas": 63631,
    "pinguinus-impennis": 94623,
    "dinornis-robustus": 314500,
    "megaloceros-giganteus": 227166,
    "ursus-spelaeus": 39097,
}


def test_catalogue_tax_ids_are_unique_and_locked() -> None:
    tax_ids = [row.tax_id for row in SPECIES]
    slugs = [row.slug for row in SPECIES]
    assert len(tax_ids) == len(set(tax_ids))
    assert len(slugs) == len(set(slugs))
    for slug, tax_id in LOCKED_TAX_IDS.items():
        assert species_by_tax_id()[tax_id].slug == slug
        assert any(row.slug == slug and row.tax_id == tax_id for row in SPECIES)
    assert 9606 not in tax_ids
    assert 9901 not in tax_ids  # Bison bison must not be used for aurochs
    assert 83618 not in tax_ids  # living plains zebra is not the quagga subspecies


def test_ancient_dna_is_not_a_sequence_type() -> None:
    values = {member.value for member in SequenceType}
    assert "ancient_dna" not in values
    assert "paleogenomics" not in values
    assert SequenceType.DNA.value == "dna"


def test_complete_mitogenome_requires_name_and_length() -> None:
    assert is_complete_mitogenome(
        definition="Raphus cucullatus complete mitochondrial genome",
        length=16_500,
    )
    assert is_complete_mitogenome(
        definition="Homo sapiens neanderthalensis mitochondrion, complete genome",
        length=16_565,
    )
    assert not is_complete_mitogenome(
        definition="Raphus cucullatus complete mitochondrial genome",
        length=800,
    )
    assert not is_complete_mitogenome(
        definition="Raphus cucullatus cytochrome b partial cds",
        length=16_500,
    )
    assert not is_complete_mitogenome(definition="complete mitochondrial genome", length=None)


def test_catalogue_rejects_chromosome_scale_and_sra_runs() -> None:
    from app.pipeline.paleogenomics.discover import NUCCORE_TERM, score_candidate

    assert sequence_length_allowed_for_catalogue(20_000, molecule="dna")
    assert not sequence_length_allowed_for_catalogue(5_000_000, molecule="dna")
    assert not sequence_length_allowed_for_catalogue(12_000, molecule="protein")
    assert sra_run_is_not_a_sequence_accession("SRR12345678")
    assert sra_run_is_not_a_sequence_accession("ERR000001")
    assert not sra_run_is_not_a_sequence_accession("NC_007596")
    assert "gss[filter]" in NUCCORE_TERM
    assert score_candidate("complete mitochondrial genome", 16500) > score_candidate(
        "NE1_segment genomic survey sequence", 50
    )


def test_introgression_is_living_human_not_neanderthal_sequence() -> None:
    assert introgression_modern_tax_id() == 9606
    assert introgression_is_not_ancient_specimen(modern_tax_id=9606, archaic_source="neanderthal")
    assert not introgression_is_not_ancient_specimen(modern_tax_id=63221, archaic_source="neanderthal")
    sources = {str(row["archaic_source"]) for row in INTROGRESSION_LOCI}
    assert "neanderthal" in sources
    assert "denisovan" in sources
    genes = [(row["archaic_source"], row["gene_name"]) for row in INTROGRESSION_LOCI]
    assert len(genes) == len(set(genes))
    for row in INTROGRESSION_LOCI:
        assert row.get("start_position") is None
        assert row.get("end_position") is None
        assert row.get("reference_build") is None


def test_living_relatives_are_not_collapsed_into_extinct_taxa() -> None:
    assert living_relative_is_not_extinct("Bos taurus", "Bos primigenius")
    assert living_relative_is_not_extinct("Equus quagga", "Equus quagga quagga")
    assert not living_relative_is_not_extinct("Bos primigenius", "Bos primigenius")


def test_narrative_evidence_levels_are_controlled_vocabulary() -> None:
    allowed = {member.value for member in EvidenceLevel}
    assert set(NARRATIVES) == {row.slug for row in SPECIES}
    for slug, claims in NARRATIVES.items():
        assert claims, slug
        for claim in claims:
            assert claim["evidence_level"] in allowed
            assert claim["evidence_level"] != "research_discussion"
            assert claim["body"].strip()


def test_dodo_narrative_rejects_madagascar_and_stupidity_myths() -> None:
    blob = " ".join(str(c["body"]) for c in NARRATIVES["raphus-cucullatus"]).lower()
    assert "mauritius" in blob
    assert "did not evolve because madagascar" in blob
    assert "lazy" not in blob
    assert SHAPIRO_2002_FLIGHT_OF_THE_DODO == 11872833


def test_neanderthal_narrative_does_not_claim_a_fixed_percentage() -> None:
    blob = " ".join(str(c["body"]) for c in NARRATIVES["homo-neanderthalensis"]).lower()
    assert "exactly 2% in all non-africans" in blob
    assert "is not an ethnic classification" in blob
    assert "contain exactly 2%" not in blob
    assert SANKARARAMAN_2014_NEANDERTHAL_ANCESTRY == 24476815


def test_normalize_doi() -> None:
    assert normalize_doi("https://doi.org/10.1111/j.1474-919x.2006.00478.x") == (
        "10.1111/j.1474-919x.2006.00478.x"
    )
    assert normalize_doi("DOI:10.1080/08912960600639400") == "10.1080/08912960600639400"
    assert normalize_doi(None) is None


def test_extract_project_accessions_does_not_invent() -> None:
    from app.pipeline.paleogenomics.semantics import extract_project_accessions, species_search_names

    projects, samples = extract_project_accessions(
        "Westbury draft genome BioProject PRJNA691254 BioSample SAMN12345678",
        "no project here",
    )
    assert projects == ["PRJNA691254"]
    assert samples == ["SAMN12345678"]
    empty_p, empty_s = extract_project_accessions("ancient DNA from a museum skin")
    assert empty_p == []
    assert empty_s == []
    names = species_search_names(
        "Thylacinus cynocephalus",
        "Thylacine",
        ("Tasmanian tiger", "Thylacine"),
    )
    assert "Thylacinus cynocephalus" in names
    assert "Thylacine" in names
    assert "Tasmanian tiger" in names
    assert names.count("Thylacine") == 1


def test_specimen_label_requires_an_explicit_voucher_or_isolate() -> None:
    from app.pipeline.paleogenomics.semantics import specimen_label_from_definition

    assert specimen_label_from_definition(
        "Smilodon populator voucher ZMA20.042 mitochondrion, complete genome"
    ) == "ZMA20.042"
    assert specimen_label_from_definition(
        "Equus burchellii quagga isolate QUAGGA mitochondrion, complete genome"
    ) == "QUAGGA"
    assert specimen_label_from_definition("museum specimen from a cave") is None
    assert specimen_label_from_definition("two similar titles are not the same specimen") is None
