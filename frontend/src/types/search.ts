import type { CategoryKey } from "@/lib/design-tokens";

/** Searchable dimensions supported by the global search. */
export type SearchType =
  | "gene"
  | "protein"
  | "dna"
  | "rna"
  | "virus"
  | "crispr"
  | "genome"
  | "accession"
  | "taxonomy";

export type ComplexityLevel = "any" | "low" | "medium" | "high";

export interface SearchFilters {
  /** Restrict to specific search types; empty = all. */
  types: SearchType[];
  organism: string;
  source: string;
  category: CategoryKey | "all";
  minLength: number | null;
  maxLength: number | null;
  complexity: ComplexityLevel;
}

/** A single result row returned by the backend. Never fabricated on the client. */
export interface SearchResult {
  id: string;
  accession: string;
  title: string;
  type: SearchType;
  organism: string;
  source: string;
  length: number;
  category: CategoryKey;
}

/** Lightweight autocomplete suggestion returned by the backend. */
export interface SearchSuggestion {
  id: string;
  label: string;
  type: SearchType | "paleogenomics";
  accession?: string;
  slug?: string;
}

/** A publication hit — real PubMed / REFERENCE records, never fabricated. */
export interface SearchPublication {
  id: string;
  pubmedId: number | null;
  doi: string | null;
  title: string;
  authors: string[];
  journal: string | null;
  year: number | null;
  url: string | null;
}

export interface SearchResponse {
  query: string;
  total: number;
  results: SearchResult[];
  /** Cursor for keyset pagination (PostgreSQL-friendly). */
  nextCursor: string | null;
  /** Publication hits related to the query (optional, additive). */
  publications?: SearchPublication[];
  publicationsTotal?: number;
  paleogenomicsProfiles?: SearchPaleogenomicsProfile[];
}

export interface SearchPaleogenomicsProfile {
  id: string;
  slug: string;
  title: string;
  scientificName: string;
  type: "paleogenomics";
}

export interface SuggestResponse {
  query: string;
  suggestions: SearchSuggestion[];
}

export const DEFAULT_FILTERS: SearchFilters = {
  types: [],
  organism: "",
  source: "all",
  category: "all",
  minLength: null,
  maxLength: null,
  complexity: "any",
};
