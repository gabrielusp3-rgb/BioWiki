export type DnaMoleculeType =
  | "gene"
  | "cds"
  | "genomic"
  | "mrna"
  | "exon"
  | "regulatory"
  | "other";

export type Strand = "+" | "-" | "unknown";

export interface DnaSequence {
  id: string;
  accession: string;
  version?: string;
  name: string;
  organism: string;
  taxId?: number;
  source: string;
  moleculeType: DnaMoleculeType;
  strand: Strand;
  length: number;
  /** GC content ratio (0–1) or null when not computed by the backend. */
  gcContent: number | null;
  updatedAt?: string;
  /** Raw residues — present only on detail responses, never fabricated. */
  sequence?: string | null;
}

export interface DnaFilters {
  organism: string;
  source: string;
  moleculeType: DnaMoleculeType | "all";
  strand: Strand | "all";
  minLength: number | null;
  maxLength: number | null;
}

export interface DnaListResponse {
  results: DnaSequence[];
  total: number;
  nextCursor: string | null;
}

export const DEFAULT_DNA_FILTERS: DnaFilters = {
  organism: "",
  source: "all",
  moleculeType: "all",
  strand: "all",
  minLength: null,
  maxLength: null,
};
