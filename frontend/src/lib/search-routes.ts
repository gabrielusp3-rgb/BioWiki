import type { CategoryKey } from "@/lib/design-tokens";
import type { SearchType } from "@/types/search";

/** Explorer route for each biological category. */
export const CATEGORY_PATH: Record<CategoryKey, string> = {
  dna: "/dna",
  rna: "/rna",
  protein: "/proteins",
  crispr: "/crispr",
  virus: "/virus",
  genome: "/genomes",
};

const SEARCH_TYPE_PATH: Partial<Record<SearchType, string>> = {
  dna: "/dna",
  rna: "/rna",
  protein: "/proteins",
  crispr: "/crispr",
  virus: "/virus",
  genome: "/genomes",
};

/**
 * Resolves a search scope to its explorer route. Scopes without a dedicated
 * explorer (gene, accession, taxonomy) fall back to the global search page.
 */
export function pathForSearchType(type: SearchType): string {
  return SEARCH_TYPE_PATH[type] ?? "/search";
}

/** Builds an explorer/search URL pre-filled with a query string. */
export function searchUrl(basePath: string, query: string): string {
  const trimmed = query.trim();
  return trimmed ? `${basePath}?q=${encodeURIComponent(trimmed)}` : basePath;
}
