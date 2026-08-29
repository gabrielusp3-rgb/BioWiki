export interface SequenceBase {
  id: string;
  type: string;
  accession: string;
  version?: string | null;
  name: string;
  organism: string;
  taxId?: number | null;
  source: string;
  length: number;
  updatedAt?: string | null;
  sequence?: string | null;
  description?: string | null;
  geneName?: string | null;
  chromosome?: string | null;
  sourceUrl?: string | null;
  annotations?: Record<string, unknown> | null;
}

export interface DnaRead extends SequenceBase {
  moleculeType?: string | null;
  strand?: string | null;
  gcContent?: number | null;
}

export interface RnaRead extends SequenceBase {
  rnaClass: string;
  isCoding: boolean;
  gcContent?: number | null;
}

export interface ProteinRead extends SequenceBase {
  gene?: string | null;
  reviewed: boolean;
  molecularWeight?: number | null;
  function?: string | null;
  pdbIds: string[];
  domains: string[];
}

export interface VirusRead extends SequenceBase {
  family: string;
  host?: string | null;
  genomeType: string;
  segment?: string | null;
  molecule: string;
  gcContent?: number | null;
}

export interface CrisprRead {
  id: string;
  type: string;
  accession: string;
  name: string;
  organism: string;
  taxId?: number | null;
  source: string;
  system: string;
  evidenceType?: string | null;
  targetGene: string;
  pam: string;
  guideLength: number;
  guideSequence?: string | null;
  genomicTarget?: string | null;
  onTargetScore?: number | null;
  offTargetScore?: number | null;
  targetSourceAccession?: string | null;
  method?: string | null;
  updatedAt?: string | null;
  description?: string | null;
  sourceUrl?: string | null;
  gcContent?: number | null;
}

export interface GenomeRead {
  id: string;
  accession: string;
  assemblyName?: string | null;
  description?: string | null;
  organism: string;
  taxId: number;
  source: string;
  assemblyLevel: string;
  totalLength?: number | null;
  chromosomeCount?: number | null;
  scaffoldCount?: number | null;
  contigCount?: number | null;
  gcContent?: number | null;
  releaseDate?: string | null;
  updatedAt?: string | null;
  sourceUrl?: string | null;
}

export interface OrganismRead {
  id: string;
  slug: string;
  scientificName: string;
  commonName?: string | null;
  taxId: number;
  rank?: string | null;
  lineage: string[];
  group: string;
  imageUrl?: string | null;
  sequenceCount?: number | null;
}

export interface PublicationRead {
  id: string;
  pubmedId?: number | null;
  doi?: string | null;
  pmcId?: string | null;
  title: string;
  abstract?: string | null;
  authors: string[];
  journal?: string | null;
  year?: number | null;
  volume?: string | null;
  pages?: string | null;
  url?: string | null;
}

export interface PublicationDetail extends PublicationRead {
  sequenceAccessions: string[];
}

export interface ListResponse<T> {
  results: T[];
  total: number;
  nextCursor?: string | null;
}

export interface OrganismListResponse {
  organisms: OrganismRead[];
  total: number;
  nextCursor?: string | null;
}

export interface CategoryStat {
  key: string;
  label: string;
  count: number;
  totalResidues: number;
}

export interface LastRun {
  sourceKey: string;
  kind: string;
  status: string;
  finishedAt?: string | null;
  created?: number | null;
  updated?: number | null;
  failed?: number | null;
}

export interface SyncInfo {
  status: "empty" | "importing" | "error" | "updated" | "connected" | string;
  activeImports: number;
  countsInSync: boolean;
  lastRun?: LastRun | null;
}

export interface DatabaseStatistics {
  totalSequences: number;
  totalResidues: number;
  organisms: number;
  genes: number;
  genomes: number;
  publications: number;
  linkedPublications: number;
  categories: CategoryStat[];
  sync: SyncInfo;
  lastUpdated?: string | null;
}

export interface SearchResult {
  id: string;
  accession: string;
  title: string;
  type: string;
  organism: string;
  source: string;
  length: number;
  category: string;
}

export interface SearchPublication {
  id: string;
  pubmedId?: number | null;
  doi?: string | null;
  title: string;
  authors: string[];
  journal?: string | null;
  year?: number | null;
  url?: string | null;
}

export interface SearchResponse {
  query: string;
  total: number;
  results: SearchResult[];
  nextCursor?: string | null;
  publications: SearchPublication[];
  publicationsTotal: number;
}

export interface SearchSuggestion {
  id: string;
  label: string;
  type: string;
  accession?: string | null;
}

export interface SuggestResponse {
  query: string;
  suggestions: SearchSuggestion[];
}
