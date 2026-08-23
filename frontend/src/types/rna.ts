export type RnaClass =
  | "mrna"
  | "trna"
  | "rrna"
  | "lncrna"
  | "mirna"
  | "snrna"
  | "other";

export interface RnaSequence {
  id: string;
  accession: string;
  version?: string;
  name: string;
  organism: string;
  taxId?: number;
  source: string;
  rnaClass: RnaClass;
  isCoding: boolean;
  length: number;
  /** GC content ratio (0–1) or null when not computed by the backend. */
  gcContent: number | null;
  updatedAt?: string;
  /** Raw residues (A/U/G/C) — present only on detail responses, never fabricated. */
  sequence?: string | null;
}

export interface RnaFilters {
  organism: string;
  source: string;
  rnaClass: RnaClass | "all";
  coding: "all" | "coding" | "noncoding";
  minLength: number | null;
  maxLength: number | null;
}

export interface RnaListResponse {
  results: RnaSequence[];
  total: number;
  nextCursor: string | null;
}

export const DEFAULT_RNA_FILTERS: RnaFilters = {
  organism: "",
  source: "all",
  rnaClass: "all",
  coding: "all",
  minLength: null,
  maxLength: null,
};
