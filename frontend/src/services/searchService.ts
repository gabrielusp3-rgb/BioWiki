import { apiGet, isApiConfigured } from "@/lib/api";
import type {
  SearchFilters,
  SearchResponse,
  SuggestResponse,
} from "@/types/search";

/**
 * Maps UI filters to the query parameters accepted by the FastAPI `/search`
 * endpoint, which is backed by PostgreSQL full-text search:
 *
 *   q          → websearch_to_tsquery over the indexed tsvector
 *   types      → filter on sequence.type (comma separated)
 *   organism   → trigram match on organism.scientific_name
 *   source     → filter on source.name
 *   category   → filter on sequence.type category
 *   min/maxLen → range predicate on sequence.length
 *   complexity → precomputed complexity bucket
 *   limit      → page size
 *   cursor     → keyset pagination cursor
 */
export function toParams(query: string, filters: SearchFilters, limit: number, cursor?: string) {
  return {
    q: query,
    types: filters.types.length ? filters.types.join(",") : undefined,
    organism: filters.organism || undefined,
    source: filters.source !== "all" ? filters.source : undefined,
    category: filters.category !== "all" ? filters.category : undefined,
    min_length: filters.minLength ?? undefined,
    max_length: filters.maxLength ?? undefined,
    complexity: filters.complexity !== "any" ? filters.complexity : undefined,
    limit,
    cursor,
  };
}

const EMPTY_RESPONSE = (query: string): SearchResponse => ({
  query,
  total: 0,
  results: [],
  nextCursor: null,
  publications: [],
  publicationsTotal: 0,
});

export async function search(
  query: string,
  filters: SearchFilters,
  options: { limit?: number; cursor?: string; signal?: AbortSignal } = {},
): Promise<SearchResponse> {
  const trimmed = query.trim();
  if (!trimmed || !isApiConfigured) return EMPTY_RESPONSE(trimmed);

  const { limit = 20, cursor, signal } = options;
  return apiGet<SearchResponse>("/search", {
    params: toParams(trimmed, filters, limit, cursor),
    signal,
  });
}

export async function suggest(
  query: string,
  options: { limit?: number; signal?: AbortSignal } = {},
): Promise<SuggestResponse> {
  const trimmed = query.trim();
  if (!trimmed || !isApiConfigured) {
    return { query: trimmed, suggestions: [] };
  }

  const { limit = 8, signal } = options;
  return apiGet<SuggestResponse>("/search/suggest", {
    params: { q: trimmed, limit },
    signal,
  });
}

export type { SearchFilters as SearchServiceFilters };
