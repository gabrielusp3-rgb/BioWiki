"""Mandatory Paleogenomics catalogue. TaxIDs are live NCBI Taxonomy identifiers."""

from __future__ import annotations

from dataclasses import dataclass

from app.models.enums import DeextinctionStatus, ExtinctionStatus, PaleogenomicSubsection


@dataclass(frozen=True)
class PaleogenomicSpecies:
    slug: str
    scientific_name: str
    common_name: str
    tax_id: int
    subsection: PaleogenomicSubsection
    extinction_status: ExtinctionStatus
    extinction_date_text: str
    geologic_period: str
    geographic_region: str
    preferred_sequence_target: int
    featured_rank: int | None
    deextinction_status: DeextinctionStatus
    synonyms: tuple[str, ...] = ()
    taxonomic_uncertainty: str | None = None
    # If False, BioWiki must not imply that authentic DNA is catalogued.
    public_dna_expected: bool = True


# NCBI Taxonomy IDs confirmed via ESummary on 2026-08-30.
SPECIES: tuple[PaleogenomicSpecies, ...] = (
    PaleogenomicSpecies(
        slug="homo-neanderthalensis",
        scientific_name="Homo sapiens neanderthalensis",
        common_name="Neanderthal",
        tax_id=63221,
        subsection=PaleogenomicSubsection.ARCHAIC_HOMININ,
        extinction_status=ExtinctionStatus.ARCHAIC_HOMININ,
        extinction_date_text="Late Pleistocene; last unambiguous fossils ~40 ka",
        geologic_period="Middle–Late Pleistocene",
        geographic_region="Eurasia",
        preferred_sequence_target=300,
        featured_rank=5,
        deextinction_status=DeextinctionStatus.NO_ACTIVE_PROGRAM,
        synonyms=("Neandertal", "Homo neanderthalensis"),
        taxonomic_uncertainty=(
            "NCBI currently ranks this taxon as a subspecies of Homo sapiens "
            "(TaxID 63221). Many papers use Homo neanderthalensis. BioWiki stores "
            "the NCBI TaxID and does not merge records with living Homo sapiens (9606)."
        ),
    ),
    PaleogenomicSpecies(
        slug="homo-denisova",
        scientific_name="Homo sapiens subsp. 'Denisova'",
        common_name="Denisovan",
        tax_id=741158,
        subsection=PaleogenomicSubsection.ARCHAIC_HOMININ,
        extinction_status=ExtinctionStatus.ARCHAIC_HOMININ,
        extinction_date_text="Late Pleistocene; last-occurrence timing remains poorly constrained",
        geologic_period="Middle–Late Pleistocene",
        geographic_region="Asia (Denisova Cave and related ancestry in Asia/Oceania)",
        preferred_sequence_target=100,
        featured_rank=6,
        deextinction_status=DeextinctionStatus.NO_ACTIVE_PROGRAM,
        synonyms=("Denisova hominin", "Denisovan", "Homo sp. Altai"),
        taxonomic_uncertainty=(
            "NCBI lists this lineage as Homo sapiens subsp. 'Denisova' (TaxID 741158). "
            "A formal species epithet is still debated; BioWiki does not invent one. "
            "Claims that Harbin/Homo longi is this lineage are recorded as debated, not as NCBI taxonomy."
        ),
    ),
    PaleogenomicSpecies(
        slug="thylacinus-cynocephalus",
        scientific_name="Thylacinus cynocephalus",
        common_name="Thylacine",
        tax_id=9275,
        subsection=PaleogenomicSubsection.EXTINCT_SPECIES,
        extinction_status=ExtinctionStatus.EXTINCT_HISTORIC,
        extinction_date_text="1936 (last captive individual, Hobart); wild extinction slightly earlier is debated",
        geologic_period="Holocene (historic extinction)",
        geographic_region="Australia and Tasmania",
        preferred_sequence_target=110,
        featured_rank=2,
        deextinction_status=DeextinctionStatus.GENOME_ENGINEERING_RESEARCH,
        synonyms=("Tasmanian tiger", "Tasmanian wolf"),
    ),
    PaleogenomicSpecies(
        slug="coelodonta-antiquitatis",
        scientific_name="Coelodonta antiquitatis",
        common_name="Woolly rhinoceros",
        tax_id=222863,
        subsection=PaleogenomicSubsection.EXTINCT_SPECIES,
        extinction_status=ExtinctionStatus.EXTINCT_PREHISTORIC,
        extinction_date_text="Late Pleistocene; regional last occurrences ~14 ka",
        geologic_period="Pleistocene",
        geographic_region="northern Eurasia",
        preferred_sequence_target=90,
        featured_rank=3,
        deextinction_status=DeextinctionStatus.NO_ACTIVE_PROGRAM,
    ),
    PaleogenomicSpecies(
        slug="raphus-cucullatus",
        scientific_name="Raphus cucullatus",
        common_name="Dodo",
        tax_id=187135,
        subsection=PaleogenomicSubsection.EXTINCT_SPECIES,
        extinction_status=ExtinctionStatus.EXTINCT_HISTORIC,
        extinction_date_text="late 17th century; last widely cited sightings ~1662–1693",
        geologic_period="Holocene (historic extinction)",
        geographic_region="Mauritius",
        preferred_sequence_target=50,
        featured_rank=1,
        deextinction_status=DeextinctionStatus.PROXY_TRAIT_ENGINEERING,
        synonyms=("Didus ineptus",),
    ),
    PaleogenomicSpecies(
        slug="mammuthus-primigenius",
        scientific_name="Mammuthus primigenius",
        common_name="Woolly mammoth",
        tax_id=37349,
        subsection=PaleogenomicSubsection.EXTINCT_SPECIES,
        extinction_status=ExtinctionStatus.EXTINCT_PREHISTORIC,
        extinction_date_text="mainland ~14–10 ka; Wrangel Island ~4 ka",
        geologic_period="Pleistocene–Holocene",
        geographic_region="Holarctic steppe-tundra",
        preferred_sequence_target=110,
        featured_rank=4,
        deextinction_status=DeextinctionStatus.GENOME_ENGINEERING_RESEARCH,
    ),
    PaleogenomicSpecies(
        slug="mammut-americanum",
        scientific_name="Mammut americanum",
        common_name="American mastodon",
        tax_id=39053,
        subsection=PaleogenomicSubsection.EXTINCT_SPECIES,
        extinction_status=ExtinctionStatus.EXTINCT_PREHISTORIC,
        extinction_date_text="end-Pleistocene ~13–10 ka in North America",
        geologic_period="Pleistocene",
        geographic_region="North America",
        preferred_sequence_target=60,
        featured_rank=None,
        deextinction_status=DeextinctionStatus.NO_ACTIVE_PROGRAM,
    ),
    PaleogenomicSpecies(
        slug="smilodon-populator",
        scientific_name="Smilodon populator",
        common_name="Smilodon",
        tax_id=339609,
        subsection=PaleogenomicSubsection.EXTINCT_SPECIES,
        extinction_status=ExtinctionStatus.EXTINCT_PREHISTORIC,
        extinction_date_text="Late Pleistocene in South America",
        geologic_period="Pleistocene",
        geographic_region="South America",
        preferred_sequence_target=50,
        featured_rank=None,
        deextinction_status=DeextinctionStatus.NO_ACTIVE_PROGRAM,
        synonyms=("saber-toothed cat", "Greater saber-toothed cat"),
    ),
    PaleogenomicSpecies(
        slug="bos-primigenius",
        scientific_name="Bos primigenius",
        common_name="Aurochs",
        tax_id=9909,
        subsection=PaleogenomicSubsection.EXTINCT_SPECIES,
        extinction_status=ExtinctionStatus.EXTINCT_HISTORIC,
        extinction_date_text="1627 (last recorded individual, Poland); not Bos taurus",
        geologic_period="Holocene (historic extinction)",
        geographic_region="Eurasia and North Africa",
        preferred_sequence_target=80,
        featured_rank=None,
        deextinction_status=DeextinctionStatus.RESEARCH_DISCUSSION,
    ),
    PaleogenomicSpecies(
        slug="equus-quagga-quagga",
        scientific_name="Equus quagga quagga",
        common_name="Quagga",
        tax_id=555873,
        subsection=PaleogenomicSubsection.EXTINCT_SPECIES,
        extinction_status=ExtinctionStatus.EXTINCT_HISTORIC,
        extinction_date_text="1883 (last captive individual); subspecies of Equus quagga",
        geologic_period="Holocene (historic extinction)",
        geographic_region="southern Africa",
        preferred_sequence_target=30,
        featured_rank=None,
        deextinction_status=DeextinctionStatus.RESEARCH_DISCUSSION,
        taxonomic_uncertainty=(
            "NCBI treats the quagga as Equus quagga quagga (TaxID 555873), a subspecies "
            "of the living plains zebra. BioWiki does not ingest Equus quagga (living) "
            "records as if they were the extinct subspecies."
        ),
    ),
    PaleogenomicSpecies(
        slug="ectopistes-migratorius",
        scientific_name="Ectopistes migratorius",
        common_name="Passenger pigeon",
        tax_id=187118,
        subsection=PaleogenomicSubsection.EXTINCT_SPECIES,
        extinction_status=ExtinctionStatus.EXTINCT_HISTORIC,
        extinction_date_text="1914 (Martha, Cincinnati Zoo)",
        geologic_period="Holocene (historic extinction)",
        geographic_region="eastern North America",
        preferred_sequence_target=60,
        featured_rank=None,
        deextinction_status=DeextinctionStatus.RESEARCH_DISCUSSION,
    ),
    PaleogenomicSpecies(
        slug="hydrodamalis-gigas",
        scientific_name="Hydrodamalis gigas",
        common_name="Steller's sea cow",
        tax_id=63631,
        subsection=PaleogenomicSubsection.EXTINCT_SPECIES,
        extinction_status=ExtinctionStatus.EXTINCT_HISTORIC,
        extinction_date_text="1768, Commander Islands, after documented hunting",
        geologic_period="Holocene (historic extinction)",
        geographic_region="North Pacific / Commander Islands",
        preferred_sequence_target=50,
        featured_rank=None,
        deextinction_status=DeextinctionStatus.NO_ACTIVE_PROGRAM,
    ),
    PaleogenomicSpecies(
        slug="pinguinus-impennis",
        scientific_name="Pinguinus impennis",
        common_name="Great auk",
        tax_id=94623,
        subsection=PaleogenomicSubsection.EXTINCT_SPECIES,
        extinction_status=ExtinctionStatus.EXTINCT_HISTORIC,
        extinction_date_text="1844 (last widely accepted breeding pair, Eldey)",
        geologic_period="Holocene (historic extinction)",
        geographic_region="North Atlantic",
        preferred_sequence_target=30,
        featured_rank=None,
        deextinction_status=DeextinctionStatus.NO_ACTIVE_PROGRAM,
    ),
    PaleogenomicSpecies(
        slug="dinornis-robustus",
        scientific_name="Dinornis robustus",
        common_name="South Island giant moa",
        tax_id=314500,
        subsection=PaleogenomicSubsection.EXTINCT_SPECIES,
        extinction_status=ExtinctionStatus.EXTINCT_HISTORIC,
        extinction_date_text="after Polynesian settlement of New Zealand; ~15th century range often cited",
        geologic_period="Holocene",
        geographic_region="New Zealand (South Island)",
        preferred_sequence_target=40,
        featured_rank=None,
        deextinction_status=DeextinctionStatus.ACTIVE_RESEARCH_PROGRAM,
        synonyms=("giant moa",),
    ),
    PaleogenomicSpecies(
        slug="megaloceros-giganteus",
        scientific_name="Megaloceros giganteus",
        common_name="Irish elk",
        tax_id=227166,
        subsection=PaleogenomicSubsection.EXTINCT_SPECIES,
        extinction_status=ExtinctionStatus.EXTINCT_PREHISTORIC,
        extinction_date_text="Late Pleistocene to early Holocene in parts of Eurasia",
        geologic_period="Pleistocene–Holocene",
        geographic_region="Eurasia",
        preferred_sequence_target=30,
        featured_rank=None,
        deextinction_status=DeextinctionStatus.NO_ACTIVE_PROGRAM,
        synonyms=("giant deer",),
    ),
    PaleogenomicSpecies(
        slug="ursus-spelaeus",
        scientific_name="Ursus spelaeus",
        common_name="Cave bear",
        tax_id=39097,
        subsection=PaleogenomicSubsection.EXTINCT_SPECIES,
        extinction_status=ExtinctionStatus.EXTINCT_PREHISTORIC,
        extinction_date_text="Late Pleistocene in many European sites",
        geologic_period="Pleistocene",
        geographic_region="Europe",
        preferred_sequence_target=60,
        featured_rank=None,
        deextinction_status=DeextinctionStatus.NO_ACTIVE_PROGRAM,
    ),
)


def species_by_slug() -> dict[str, PaleogenomicSpecies]:
    return {row.slug: row for row in SPECIES}


def species_by_tax_id() -> dict[int, PaleogenomicSpecies]:
    return {row.tax_id: row for row in SPECIES}


HOMO_SAPIENS_TAX_ID = 9606

PUBMED_LIMITS: dict[str, int] = {
    "homo-neanderthalensis": 120,
    "homo-denisova": 80,
    "thylacinus-cynocephalus": 90,
    "coelodonta-antiquitatis": 90,
    "raphus-cucullatus": 90,
    "mammuthus-primigenius": 90,
}
DEFAULT_PUBMED_LIMIT = 50
GENOME_ASSEMBLY_LIMIT = 8
