export interface ProteinSequence {
  id: string;
  accession: string;
  name: string;
  gene?: string;
  organism: string;
  taxId?: number;
  source: string;
  /** UniProt review status: Swiss-Prot (reviewed) vs TrEMBL (unreviewed). */
  reviewed: boolean;
  /** Length in amino acid residues. */
  length: number;
  /** Molecular weight in Daltons, or null when not provided. */
  molecularWeight: number | null;
  function?: string | null;
  /** Related PDB structure identifiers. */
  pdbIds: string[];
  /** Domain / family annotations (Pfam, InterPro). */
  domains: string[];
  updatedAt?: string;
  /** Amino acid residues — present only on detail responses, never fabricated. */
  sequence?: string | null;
}

export interface ProteinFilters {
  organism: string;
  source: string;
  reviewed: "all" | "reviewed" | "unreviewed";
  structure: "all" | "with" | "without";
  minLength: number | null;
  maxLength: number | null;
}

export interface ProteinListResponse {
  results: ProteinSequence[];
  total: number;
  nextCursor: string | null;
}

export const DEFAULT_PROTEIN_FILTERS: ProteinFilters = {
  organism: "",
  source: "all",
  reviewed: "all",
  structure: "all",
  minLength: null,
  maxLength: null,
};
