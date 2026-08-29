export type CasSystem = "cas9" | "cas12a" | "cas13" | "base_editor" | "other";

export type CrisprEvidenceType =
  | "natural_crispr_element"
  | "experimental_guide"
  | "computational_target";

export interface CrisprGuide {
  id: string;
  accession: string;
  name: string;
  organism: string;
  taxId?: number;
  source: string;
  system: CasSystem;
  evidenceType?: CrisprEvidenceType;
  targetGene: string;
  /** Protospacer adjacent motif (e.g. NGG). */
  pam: string;
  guideLength: number;
  /** Guide/spacer residues — present only on detail responses, never fabricated. */
  guideSequence?: string | null;
  /** Genomic target coordinates as provided by the source (e.g. chr7:5,530,600). */
  genomicTarget?: string | null;
  /**
   * Efficiency / specificity scores. Sourced from the backend only — never
   * computed or invented on the client (no fictitious scoring algorithms).
   */
  onTargetScore: number | null;
  offTargetScore: number | null;
  targetSourceAccession?: string | null;
  targetTaxId?: number | null;
  sourcePmid?: number | null;
  method?: string | null;
  updatedAt?: string;
}

export interface CrisprFilters {
  organism: string;
  source: string;
  system: CasSystem | "all";
  evidenceType: CrisprEvidenceType | "all";
  targetGene: string;
  pam: string;
  minLength: number | null;
  maxLength: number | null;
}

export interface CrisprListResponse {
  results: CrisprGuide[];
  total: number;
  nextCursor: string | null;
}

export const DEFAULT_CRISPR_FILTERS: CrisprFilters = {
  organism: "",
  source: "all",
  system: "all",
  evidenceType: "all",
  targetGene: "",
  pam: "",
  minLength: null,
  maxLength: null,
};
