export type PaleogenomicSubsection =
  | "extinct_species"
  | "archaic_hominin"
  | "ancient_dna"
  | "archaic_introgression";

export type ExtinctionStatus =
  | "extinct"
  | "extinct_prehistoric"
  | "extinct_historic"
  | "archaic_hominin";

export type EvidenceLevel =
  | "consensus"
  | "strong_evidence"
  | "supported_hypothesis"
  | "debated"
  | "unknown";

export type DeextinctionStatus =
  | "no_active_program"
  | "research_discussion"
  | "active_research_program"
  | "genome_engineering_research"
  | "reproductive_technology_research"
  | "proxy_trait_engineering"
  | "reintroduction_planning"
  | "unknown";

export interface PaleogenomicClaimSource {
  pubmedId: number | null;
  doi: string | null;
  url: string | null;
  label: string | null;
  publicationId: string | null;
}

export interface PaleogenomicClaim {
  sectionKey: string;
  title: string;
  body: string;
  evidenceLevel: EvidenceLevel | string;
  sortOrder: number;
  lastReviewedOn: string | null;
  sources: PaleogenomicClaimSource[];
}

export interface PaleogenomicSpeciesCard {
  slug: string;
  commonName: string;
  scientificName: string;
  taxId: number;
  subsection: PaleogenomicSubsection | string;
  extinctionStatus: ExtinctionStatus | string | null;
  extinctionDateText: string | null;
  geologicPeriod: string | null;
  geographicRegion: string | null;
  featuredRank: number | null;
  deextinctionStatus: DeextinctionStatus | string;
  paleogenomicDataAvailable: boolean;
  taxonomicUncertainty: string | null;
  sequenceCount: number;
  assemblyCount: number;
  publicationCount: number;
  mitogenomeCount: number;
}

export interface PaleogenomicOverview {
  speciesCount: number;
  archaicHomininCount: number;
  extinctSpeciesCount: number;
  sequenceCount: number;
  assemblyCount: number;
  publicationCount: number;
  introgressionCount: number;
  projectCount: number;
  lastReviewedOn: string | null;
}

export interface PaleogenomicLanding {
  overview: PaleogenomicOverview;
  featured: PaleogenomicSpeciesCard[];
  species: PaleogenomicSpeciesCard[];
  notes: string[];
}

export interface PaleogenomicSpeciesList {
  results: PaleogenomicSpeciesCard[];
  total: number;
  nextCursor: string | null;
}

export interface PaleogenomicSequenceRow {
  id: string;
  accession: string;
  name: string;
  seqType: string;
  length: number | null;
  recordKind: string;
  isCompleteMitogenome: boolean;
  specimenLabel: string | null;
  biosample: string | null;
  bioproject: string | null;
  sourceUrl: string | null;
}

export interface PaleogenomicSequenceList {
  results: PaleogenomicSequenceRow[];
  total: number;
  nextCursor: string | null;
}

export interface PaleogenomicProject {
  bioproject: string | null;
  biosample: string | null;
  runAccession: string | null;
  experimentAccession: string | null;
  libraryStrategy: string | null;
  sourceUrl: string | null;
  notes: string | null;
  controlledAccess: boolean;
}

export interface PaleogenomicProjectList {
  results: PaleogenomicProject[];
  total: number;
  nextCursor: string | null;
}

export interface PaleogenomicIntrogression {
  id: string;
  archaicSource: string;
  geneName: string | null;
  locusName: string | null;
  referenceBuild: string | null;
  chromosome: string | null;
  startPosition: number | null;
  endPosition: number | null;
  pubmedId: number | null;
  doi: string | null;
  method: string | null;
  evidenceNotes: string;
  sourceDataset: string | null;
  modernScientificName: string;
}

export interface PaleogenomicIntrogressionList {
  results: PaleogenomicIntrogression[];
  total: number;
  nextCursor: string | null;
  note: string;
}

export interface PaleogenomicSpeciesDetail {
  slug: string;
  commonName: string;
  scientificName: string;
  taxId: number;
  subsection: string;
  organism: {
    id: string;
    slug: string;
    scientificName: string;
    taxId: number;
  };
  extinctionStatus: string | null;
  extinctionDateText: string | null;
  geologicPeriod: string | null;
  geographicRegion: string | null;
  deextinctionStatus: string;
  paleogenomicDataAvailable: boolean;
  taxonomicUncertainty: string | null;
  lastReviewedOn: string | null;
  preferredSequenceTarget: number;
  sequenceCount: number;
  assemblyCount: number;
  publicationCount: number;
  mitogenomeCount: number;
  projectCount: number;
  claims: PaleogenomicClaim[];
  introgressionCount: number | null;
  introgressionNote: string | null;
}

export interface PaleogenomicsListFilters {
  q?: string;
  subsection?: string;
  extinctionStatus?: string;
  geographicRegion?: string;
  deextinction?: string;
  dnaAvailable?: boolean;
  assemblyAvailable?: boolean;
}
