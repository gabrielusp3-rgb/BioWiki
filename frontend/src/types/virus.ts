export type GenomeType =
  | "dsDNA"
  | "ssDNA"
  | "dsRNA"
  | "ssRNA+"
  | "ssRNA-"
  | "ssRNA-RT"
  | "dsDNA-RT"
  | "other";

export interface VirusSequence {
  id: string;
  accession: string;
  version?: string;
  name: string;
  /** Scientific name of the virus. */
  organism: string;
  taxId?: number;
  source: string;
  family: string;
  host?: string | null;
  genomeType: GenomeType;
  /** Molecule alphabet of the stored residues. */
  molecule: "dna" | "rna";
  segment?: string | null;
  length: number;
  updatedAt?: string;
  /** Raw residues — present only on detail responses, never fabricated. */
  sequence?: string | null;
}

export interface VirusFilters {
  family: string;
  host: string;
  source: string;
  genomeType: GenomeType | "all";
  minLength: number | null;
  maxLength: number | null;
}

export interface VirusListResponse {
  results: VirusSequence[];
  total: number;
  nextCursor: string | null;
}

export const DEFAULT_VIRUS_FILTERS: VirusFilters = {
  family: "",
  host: "",
  source: "all",
  genomeType: "all",
  minLength: null,
  maxLength: null,
};
