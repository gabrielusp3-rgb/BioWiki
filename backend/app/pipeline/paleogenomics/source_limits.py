"""Source-exhaustion records for Paleogenomics nuccore discovery.

Preferred sequence targets in catalogue.py are discovery goals, not quotas.
These rows document NCBI searches performed on 2026-08-30. They do not invent
accessions. Live catalogue membership counts belong in the audit, not here.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.pipeline.paleogenomics.catalogue import species_by_slug
from app.pipeline.paleogenomics.discover import NUCCORE_TERM

VERIFIED_ON = date(2026, 8, 30)
ARCHIVE = "NCBI GenBank/RefSeq nuccore"
FILTERS = (
    "txid{tax_id}[Organism:noexp] NOT wgs[filter] NOT tsa[filter] NOT sra[filter] "
    "NOT gss[filter] NOT pat[filter]"
)


@dataclass(frozen=True)
class SourceLimitRecord:
    slug: str
    tax_id: int
    preferred_target: int
    filtered_nuccore_hits: int
    unfiltered_nuccore_hits: int
    accepted_accessions: tuple[str, ...]
    rejected_reasons: tuple[str, ...]
    bioproject_hits: int
    genome_assembly_in_ncbi_datasets: bool | None
    public_nuccore_exhausted: bool
    notes: str

    @property
    def search_term(self) -> str:
        return NUCCORE_TERM.format(tax_id=self.tax_id)


# Accessions listed for exhausted taxa are the complete filtered nuccore set
# returned by NCBI ESearch on VERIFIED_ON (TaxID-locked, residues-bearing INSDC
# records). They are identifiers, not newly manufactured sequences.
SOURCE_LIMITS: tuple[SourceLimitRecord, ...] = (
    SourceLimitRecord(
        slug="raphus-cucullatus",
        tax_id=187135,
        preferred_target=50,
        filtered_nuccore_hits=4,
        unfiltered_nuccore_hits=4,
        accepted_accessions=("NC_031864", "KX902236", "AF483338", "AF483301"),
        rejected_reasons=(
            "no additional nuccore records for TaxID 187135",
            "SRA/WGS not eligible as Sequence rows",
        ),
        bioproject_hits=1,
        genome_assembly_in_ncbi_datasets=False,
        public_nuccore_exhausted=True,
        notes=(
            "Four validated public nuccore records: two complete mitogenomes "
            "(KX902236 and RefSeq NC_031864) plus partial cytb AF483338 and 12S "
            "AF483301. BioProject metadata exists; no chromosome-scale NCBI Assembly."
        ),
    ),
    SourceLimitRecord(
        slug="equus-quagga-quagga",
        tax_id=555873,
        preferred_target=30,
        filtered_nuccore_hits=3,
        unfiltered_nuccore_hits=3,
        accepted_accessions=("NC_044858", "JX312733", "KM881680"),
        rejected_reasons=(
            "no additional nuccore records for TaxID 555873",
            "living Equus quagga (not this subspecies) is out of scope",
        ),
        bioproject_hits=0,
        genome_assembly_in_ncbi_datasets=False,
        public_nuccore_exhausted=True,
        notes=(
            "Three TaxID-555873 nuccore records. GenBank titles may still say "
            "Equus burchellii quagga; NCBI Taxonomy for these GIs is 555873. "
            "Living plains-zebra records must not be ingested as extinct-quagga DNA."
        ),
    ),
    SourceLimitRecord(
        slug="smilodon-populator",
        tax_id=339609,
        preferred_target=50,
        filtered_nuccore_hits=12,
        unfiltered_nuccore_hits=12,
        accepted_accessions=(
            "BK064869",
            "MF871700",
            "DQ097174",
            "DQ097169",
            "DQ097167",
            "KU884304",
            "KU884303",
            "KU884302",
            "KU884301",
            "KU884300",
            "DQ097171",
            "DQ097165",
        ),
        rejected_reasons=("no additional nuccore records for TaxID 339609",),
        bioproject_hits=1,
        genome_assembly_in_ncbi_datasets=False,
        public_nuccore_exhausted=True,
        notes=(
            "Twelve public nuccore records, mostly short mitochondrial fragments plus "
            "one complete mitogenome (BK064869) and a partial mitogenome (MF871700). "
            "A nuclear draft genome is documented as BioProject metadata, not as "
            "gigabase Sequence residues."
        ),
    ),
    SourceLimitRecord(
        slug="homo-denisova",
        tax_id=741158,
        preferred_target=100,
        filtered_nuccore_hits=8,
        unfiltered_nuccore_hits=8,
        accepted_accessions=(
            "NC_013993",
            "FN673705",
            "FR695060",
            "KT780370",
            "KX663333",
            "MT576651",
            "MT576652",
            "MT576653",
        ),
        rejected_reasons=(
            "no additional nuccore records for TaxID 741158",
            "high-coverage nuclear genomes are BioProject/SRA, not nuccore Sequence rows",
        ),
        bioproject_hits=11,
        genome_assembly_in_ncbi_datasets=False,
        public_nuccore_exhausted=True,
        notes=(
            "Public nuccore for TaxID 741158 is mitochondrial genomes from Denisova Cave "
            "specimens. Nuclear Denisovan genomes remain BioProject/SRA metadata."
        ),
    ),
    SourceLimitRecord(
        slug="coelodonta-antiquitatis",
        tax_id=222863,
        preferred_target=90,
        filtered_nuccore_hits=87,
        unfiltered_nuccore_hits=87,
        accepted_accessions=(),
        rejected_reasons=("filtered nuccore set equals the discovery harvest",),
        bioproject_hits=3,
        genome_assembly_in_ncbi_datasets=False,
        public_nuccore_exhausted=True,
        notes=(
            "Filtered nuccore hit count equals the public TaxID set (87). Preferred "
            "target 90 is a goal, not a quota. High-coverage nuclear genomes including "
            "the 2026 Tumat wolf-stomach specimen are not manufactured as Sequence rows."
        ),
    ),
    SourceLimitRecord(
        slug="megaloceros-giganteus",
        tax_id=227166,
        preferred_target=30,
        filtered_nuccore_hits=38,
        unfiltered_nuccore_hits=40,
        accepted_accessions=(),
        rejected_reasons=(
            "two unfiltered records excluded by WGS/TSA/SRA/GSS/patent filters",
        ),
        bioproject_hits=1,
        genome_assembly_in_ncbi_datasets=True,
        public_nuccore_exhausted=False,
        notes=(
            "Filtered nuccore (38) exceeds the preferred target (30). Remainder ingest "
            "adds authentic records up to that discovery goal without inventing accessions."
        ),
    ),
    SourceLimitRecord(
        slug="thylacinus-cynocephalus",
        tax_id=9275,
        preferred_target=110,
        filtered_nuccore_hits=84,
        unfiltered_nuccore_hits=92,
        accepted_accessions=(),
        rejected_reasons=("WGS/TSA/SRA/GSS/patent filters removed 8 unfiltered hits",),
        bioproject_hits=6,
        genome_assembly_in_ncbi_datasets=True,
        public_nuccore_exhausted=True,
        notes=(
            "Filtered public nuccore is 84 records. The preferred target of 110 exceeds "
            "authentic INSDC diversity after filters. Remainder ingest tags any filtered "
            "records not yet in membership, then stops."
        ),
    ),
    SourceLimitRecord(
        slug="ectopistes-migratorius",
        tax_id=187118,
        preferred_target=60,
        filtered_nuccore_hits=59,
        unfiltered_nuccore_hits=59,
        accepted_accessions=(),
        rejected_reasons=(),
        bioproject_hits=9,
        genome_assembly_in_ncbi_datasets=False,
        public_nuccore_exhausted=True,
        notes=(
            "Filtered nuccore is 59. Preferred target 60 is one above authentic public "
            "diversity. Remainder ingest tags any untagged authentic records, then stops."
        ),
    ),
)


def source_limit_for(slug: str) -> SourceLimitRecord | None:
    return next((row for row in SOURCE_LIMITS if row.slug == slug), None)


def exhausted_slugs() -> tuple[str, ...]:
    return tuple(row.slug for row in SOURCE_LIMITS if row.public_nuccore_exhausted)


def preferred_targets_are_not_quotas() -> bool:
    """A target larger than authentic public nuccore is allowed and must not be filled by invention."""
    return any(row.filtered_nuccore_hits < row.preferred_target for row in SOURCE_LIMITS)


def locked_source_limit_tax_ids_match_catalogue() -> bool:
    lookup = species_by_slug()
    return all(lookup[row.slug].tax_id == row.tax_id for row in SOURCE_LIMITS)
