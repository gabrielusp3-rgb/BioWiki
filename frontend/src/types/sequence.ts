/**
 * Generic sequence detail record returned by `/sequences/{accession}`.
 * The backend serves the category-specific DTO plus a `type` discriminator;
 * category-specific fields are optional here and rendered only when present.
 */
export type SequenceDetailType =
  | "dna"
  | "rna"
  | "protein"
  | "crispr"
  | "virus"
  | "genome"
  | "peptide";

export interface SequenceDetail {
  id: string;
  type: SequenceDetailType;
  accession: string;
  version?: string | null;
  name: string;
  organism: string;
  taxId?: number | null;
  source: string;
  length?: number;
  updatedAt?: string | null;
  /** Raw residues — present on detail responses; never fabricated. */
  sequence?: string | null;
  description?: string | null;
  geneName?: string | null;
  chromosome?: string | null;
  sourceUrl?: string | null;
  gcContent?: number | null;
  /** Structured annotations copied verbatim from the source record. */
  annotations?: Record<string, unknown> | null;

  // DNA
  moleculeType?: string;
  strand?: string;
  // RNA
  rnaClass?: string;
  isCoding?: boolean;
  // Protein
  gene?: string | null;
  reviewed?: boolean;
  molecularWeight?: number | null;
  function?: string | null;
  pdbIds?: string[];
  domains?: string[];
  // CRISPR
  system?: string;
  evidenceType?: string | null;
  targetGene?: string;
  pam?: string;
  guideLength?: number;
  guideSequence?: string | null;
  genomicTarget?: string | null;
  onTargetScore?: number | null;
  offTargetScore?: number | null;
  targetSourceAccession?: string | null;
  method?: string | null;
  // Virus
  family?: string;
  host?: string | null;
  genomeType?: string;
  segment?: string | null;
  molecule?: string;
}

/** Minimal shape shared by every category list row (for organism pages). */
export interface SequenceSummary {
  id: string;
  accession: string;
  name: string;
  organism: string;
  source: string;
  length?: number;
  guideLength?: number;
}

export interface SequenceSummaryListResponse {
  results: SequenceSummary[];
  total: number;
  nextCursor: string | null;
}

export interface GenomeAssembly {
  id: string;
  accession: string;
  assemblyName: string | null;
  description: string | null;
  organism: string;
  taxId: number;
  source: string;
  assemblyLevel: string;
  totalLength: number | null;
  chromosomeCount: number | null;
  gcContent: number | null;
  releaseDate: string | null;
  sourceUrl: string | null;
  updatedAt: string | null;
}

export interface GenomeListResponse {
  results: GenomeAssembly[];
  total: number;
  nextCursor: string | null;
}
