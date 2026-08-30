from __future__ import annotations

import uuid
from datetime import date

from app.schemas.common import CamelModel
from app.schemas.organism import OrganismRead


class PaleogenomicClaimSourceRead(CamelModel):
    pubmed_id: int | None = None
    doi: str | None = None
    url: str | None = None
    label: str | None = None
    publication_id: uuid.UUID | None = None


class PaleogenomicClaimRead(CamelModel):
    section_key: str
    title: str
    body: str
    evidence_level: str
    sort_order: int
    last_reviewed_on: date | None = None
    sources: list[PaleogenomicClaimSourceRead] = []


class PaleogenomicSpeciesCard(CamelModel):
    slug: str
    common_name: str
    scientific_name: str
    tax_id: int
    subsection: str
    extinction_status: str | None = None
    extinction_date_text: str | None = None
    geologic_period: str | None = None
    geographic_region: str | None = None
    featured_rank: int | None = None
    deextinction_status: str
    paleogenomic_data_available: bool
    taxonomic_uncertainty: str | None = None
    sequence_count: int = 0
    assembly_count: int = 0
    publication_count: int = 0
    mitogenome_count: int = 0


class PaleogenomicOverview(CamelModel):
    species_count: int
    archaic_hominin_count: int
    extinct_species_count: int
    sequence_count: int
    assembly_count: int
    publication_count: int
    introgression_count: int
    project_count: int
    last_reviewed_on: date | None = None


class PaleogenomicLanding(CamelModel):
    overview: PaleogenomicOverview
    featured: list[PaleogenomicSpeciesCard]
    species: list[PaleogenomicSpeciesCard]
    notes: list[str] = []


class PaleogenomicSpeciesList(CamelModel):
    results: list[PaleogenomicSpeciesCard]
    total: int
    next_cursor: str | None = None


class PaleogenomicSequenceRow(CamelModel):
    id: uuid.UUID
    accession: str
    name: str
    seq_type: str
    length: int | None = None
    record_kind: str
    is_complete_mitogenome: bool
    specimen_label: str | None = None
    biosample: str | None = None
    bioproject: str | None = None
    source_url: str | None = None


class PaleogenomicSequenceList(CamelModel):
    results: list[PaleogenomicSequenceRow]
    total: int
    next_cursor: str | None = None


class PaleogenomicProjectRead(CamelModel):
    bioproject: str | None = None
    biosample: str | None = None
    run_accession: str | None = None
    experiment_accession: str | None = None
    library_strategy: str | None = None
    source_url: str | None = None
    notes: str | None = None
    controlled_access: bool = False


class PaleogenomicProjectList(CamelModel):
    results: list[PaleogenomicProjectRead]
    total: int
    next_cursor: str | None = None


class PaleogenomicIntrogressionRead(CamelModel):
    id: uuid.UUID
    archaic_source: str
    gene_name: str | None = None
    locus_name: str | None = None
    reference_build: str | None = None
    chromosome: str | None = None
    start_position: int | None = None
    end_position: int | None = None
    pubmed_id: int | None = None
    doi: str | None = None
    method: str | None = None
    evidence_notes: str
    source_dataset: str | None = None
    modern_scientific_name: str


class PaleogenomicIntrogressionList(CamelModel):
    results: list[PaleogenomicIntrogressionRead]
    total: int
    next_cursor: str | None = None
    note: str


class PaleogenomicSpeciesDetail(CamelModel):
    slug: str
    common_name: str
    scientific_name: str
    tax_id: int
    subsection: str
    organism: OrganismRead
    extinction_status: str | None = None
    extinction_date_text: str | None = None
    geologic_period: str | None = None
    geographic_region: str | None = None
    deextinction_status: str
    paleogenomic_data_available: bool
    taxonomic_uncertainty: str | None = None
    last_reviewed_on: date | None = None
    preferred_sequence_target: int
    sequence_count: int
    assembly_count: int
    publication_count: int
    mitogenome_count: int
    project_count: int
    claims: list[PaleogenomicClaimRead]
    introgression_count: int | None = None
    introgression_note: str | None = None
