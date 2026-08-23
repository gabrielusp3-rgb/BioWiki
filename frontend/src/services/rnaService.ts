import { apiGet, isApiConfigured } from "@/lib/api";
import type { RnaFilters, RnaListResponse, RnaSequence } from "@/types/rna";

/**
 * RNA data access.
 * Backed by the FastAPI `/sequences` endpoint (type=rna) over PostgreSQL.
 * Returns empty, honest results when the API is not configured.
 */
function toParams(query: string, filters: RnaFilters, limit: number, cursor?: string) {
  return {
    type: "rna",
    q: query || undefined,
    organism: filters.organism || undefined,
    source: filters.source !== "all" ? filters.source : undefined,
    rna_class: filters.rnaClass !== "all" ? filters.rnaClass : undefined,
    coding:
      filters.coding === "all" ? undefined : filters.coding === "coding" ? "true" : "false",
    min_length: filters.minLength ?? undefined,
    max_length: filters.maxLength ?? undefined,
    limit,
    cursor,
  };
}

const EMPTY: RnaListResponse = { results: [], total: 0, nextCursor: null };

export async function listRna(
  query: string,
  filters: RnaFilters,
  options: { limit?: number; cursor?: string; signal?: AbortSignal } = {},
): Promise<RnaListResponse> {
  if (!isApiConfigured) return EMPTY;
  const { limit = 20, cursor, signal } = options;
  return apiGet<RnaListResponse>("/sequences", {
    params: toParams(query.trim(), filters, limit, cursor),
    signal,
  });
}

export async function getRna(
  accession: string,
  signal?: AbortSignal,
): Promise<RnaSequence | null> {
  if (!isApiConfigured) return null;
  return apiGet<RnaSequence>(`/sequences/${encodeURIComponent(accession)}`, { signal });
}
