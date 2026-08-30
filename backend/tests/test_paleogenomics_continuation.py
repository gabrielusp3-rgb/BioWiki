"""Continuation requirements: identities, source limits, de-extinction, provenance."""

from __future__ import annotations

from app.models.enums import DeextinctionStatus, SequenceType
from app.pipeline.paleogenomics.catalogue import SPECIES, species_by_slug
from app.pipeline.paleogenomics.citations import (
    GUDJONSDOTTIR_2026_WOOLLY_RHINO_INBREEDING,
    NATURE_2026_SYNTHETIC_EGG,
    NATURE_BIOTECH_2025_COLOSSAL_DODO,
    ZEBERG_2020_COVID_RISK_HAPLOTYPE,
    ZHOU_2021_OAS1_NEANDERTHAL,
)
from app.pipeline.paleogenomics.discover import NUCCORE_TERM
from app.pipeline.paleogenomics.introgression import INTROGRESSION_LOCI
from app.pipeline.paleogenomics.narratives import NARRATIVES
from app.pipeline.paleogenomics.source_limits import (
    SOURCE_LIMITS,
    VERIFIED_ON,
    exhausted_slugs,
    locked_source_limit_tax_ids_match_catalogue,
    preferred_targets_are_not_quotas,
    source_limit_for,
)
from app.pipeline.paleogenomics.semantics import sra_run_is_not_a_sequence_accession

REQUIRED_SECTIONS = {
    "overview",
    "evolution",
    "range",
    "ecology",
    "extinction",
    "paleogenomics",
    "significance",
    "modern",
    "deextinction",
}

PRIORITY_SLUGS = (
    "raphus-cucullatus",
    "thylacinus-cynocephalus",
    "coelodonta-antiquitatis",
    "homo-neanderthalensis",
    "mammuthus-primigenius",
    "dinornis-robustus",
)


def test_exactly_sixteen_locked_profiles() -> None:
    assert len(SPECIES) == 16
    slugs = [row.slug for row in SPECIES]
    assert len(set(slugs)) == 16
    assert set(slugs) == set(NARRATIVES)


def test_preferred_targets_are_metadata_not_quotas() -> None:
    dodo = species_by_slug()["raphus-cucullatus"]
    assert dodo.preferred_sequence_target == 50
    record = source_limit_for("raphus-cucullatus")
    assert record is not None
    assert record.filtered_nuccore_hits == 4
    assert record.filtered_nuccore_hits < dodo.preferred_sequence_target
    assert preferred_targets_are_not_quotas()
    assert locked_source_limit_tax_ids_match_catalogue()


def test_source_exhausted_species_are_documented() -> None:
    assert VERIFIED_ON.isoformat() == "2026-08-30"
    assert "gss[filter]" in NUCCORE_TERM
    dodo = source_limit_for("raphus-cucullatus")
    quagga = source_limit_for("equus-quagga-quagga")
    smilodon = source_limit_for("smilodon-populator")
    denisovan = source_limit_for("homo-denisova")
    assert dodo and dodo.public_nuccore_exhausted
    assert dodo.accepted_accessions == ("NC_031864", "KX902236", "AF483338", "AF483301")
    assert quagga and quagga.filtered_nuccore_hits == 3
    assert smilodon and smilodon.filtered_nuccore_hits == 12
    assert denisovan and denisovan.filtered_nuccore_hits == 8
    assert "raphus-cucullatus" in exhausted_slugs()
    for row in SOURCE_LIMITS:
        assert row.tax_id == species_by_slug()[row.slug].tax_id
        assert row.preferred_target == species_by_slug()[row.slug].preferred_sequence_target


def test_no_sra_runs_as_sequence_accessions() -> None:
    assert sra_run_is_not_a_sequence_accession("SRR12345678")
    assert SequenceType.GENOME.value != "ancient_dna"


def test_every_profile_has_source_backed_narrative_structure() -> None:
    for species in SPECIES:
        keys = {str(claim["section_key"]) for claim in NARRATIVES[species.slug]}
        missing = REQUIRED_SECTIONS - keys
        assert not missing, f"{species.slug} missing {missing}"
        for claim in NARRATIVES[species.slug]:
            has_source = bool(claim.get("pubmed_ids") or claim.get("dois") or claim.get("urls"))
            if claim["section_key"] in {"overview", "evolution", "extinction", "paleogenomics"}:
                assert has_source, f"{species.slug} {claim['section_key']} needs a source"


def test_priority_profiles_include_uncertainty_and_citations() -> None:
    for slug in PRIORITY_SLUGS:
        keys = {str(claim["section_key"]) for claim in NARRATIVES[slug]}
        assert "uncertainty" in keys, slug
        assert "deextinction" in keys, slug


def test_woolly_rhino_2026_paper_is_cited() -> None:
    assert GUDJONSDOTTIR_2026_WOOLLY_RHINO_INBREEDING == 41530912
    blob = " ".join(str(c["body"]) for c in NARRATIVES["coelodonta-antiquitatis"]).lower()
    assert "14,400" in blob or "14400" in blob or "14.400" in blob or "14 400" in blob
    assert "wolf" in blob
    assert "inbreeding" in blob
    pmids: list[int] = []
    for claim in NARRATIVES["coelodonta-antiquitatis"]:
        pmids.extend(int(p) for p in claim.get("pubmed_ids") or [])
    assert 41530912 in pmids


def test_moa_deextinction_status_is_active_research_not_resurrection() -> None:
    moa = species_by_slug()["dinornis-robustus"]
    assert moa.deextinction_status == DeextinctionStatus.ACTIVE_RESEARCH_PROGRAM
    assert moa.deextinction_status != DeextinctionStatus.NO_ACTIVE_PROGRAM
    blob = " ".join(str(c["body"]) for c in NARRATIVES["dinornis-robustus"]).lower()
    assert "resurrected" in blob  # negation / caution in the narrative
    assert "not been resurrected" in blob or "has been resurrected" in blob
    assert "caution" in blob
    deext = next(c for c in NARRATIVES["dinornis-robustus"] if c["section_key"] == "deextinction")
    assert deext["evidence_level"] == "supported_hypothesis"
    assert NATURE_2026_SYNTHETIC_EGG in deext["pubmed_ids"]
    assert any("colossal.com/moa" in str(u) for u in deext.get("urls") or [])


def test_deextinction_literature_distinguishes_proxy_from_historical_species() -> None:
    assert NATURE_BIOTECH_2025_COLOSSAL_DODO == 39953226
    dodo = " ".join(str(c["body"]) for c in NARRATIVES["raphus-cucullatus"]).lower()
    mammoth = " ".join(str(c["body"]) for c in NARRATIVES["mammuthus-primigenius"]).lower()
    thylacine = " ".join(str(c["body"]) for c in NARRATIVES["thylacinus-cynocephalus"]).lower()
    for blob in (dodo, mammoth, thylacine):
        assert "not" in blob
        assert "exact" in blob or "automatically" in blob or "proxy" in blob


def test_introgression_additions_are_gene_level_and_publication_backed() -> None:
    genes = {(row["archaic_source"], row["gene_name"]) for row in INTROGRESSION_LOCI}
    assert ("neanderthal", "LZTFL1") in genes
    assert ("denisovan", "WARS2") in genes
    assert ("denisovan", "EPAS1") in genes
    lztfl1 = next(row for row in INTROGRESSION_LOCI if row["gene_name"] == "LZTFL1")
    assert lztfl1["pubmed_id"] == ZEBERG_2020_COVID_RISK_HAPLOTYPE == 32998156
    oas1 = next(row for row in INTROGRESSION_LOCI if row["gene_name"] == "OAS1")
    assert "33633408" in str(oas1["evidence_notes"])
    assert ZHOU_2021_OAS1_NEANDERTHAL == 33633408
    for row in INTROGRESSION_LOCI:
        assert row["pubmed_id"]
        assert row.get("start_position") is None


def test_quagga_and_neanderthal_taxonomy_are_not_collapsed() -> None:
    assert species_by_slug()["equus-quagga-quagga"].tax_id == 555873
    assert species_by_slug()["homo-neanderthalensis"].tax_id == 63221
    assert species_by_slug()["homo-denisova"].tax_id == 741158
    assert all(row.tax_id != 9606 for row in SPECIES)
    assert all(row.tax_id != 83618 for row in SPECIES)
