import { apiGet, isApiConfigured } from "@/lib/api";
import type { ProteinFilters, ProteinListResponse, ProteinSequence } from "@/types/protein";

/**
 * Protein data access.
 * Backed by the FastAPI `/proteins` endpoint over PostgreSQL. Returns empty,
 * honest results when the API is not configured — no records are fabricated.
 */
function toParams(query: string, filters: ProteinFilters, limit: number, cursor?: string) {
  return {
    q: query || undefined,
    organism: filters.organism || undefined,
    source: filters.source !== "all" ? filters.source : undefined,
    reviewed:
      filters.reviewed === "all" ? undefined : filters.reviewed === "reviewed" ? "true" : "false",
    has_structure:
      filters.structure === "all" ? undefined : filters.structure === "with" ? "true" : "false",
    min_length: filters.minLength ?? undefined,
    max_length: filters.maxLength ?? undefined,
    limit,
    cursor,
  };
}

const EMPTY: ProteinListResponse = { results: [], total: 0, nextCursor: null };

export async function listProteins(
  query: string,
  filters: ProteinFilters,
  options: { limit?: number; cursor?: string; signal?: AbortSignal } = {},
): Promise<ProteinListResponse> {
  if (!isApiConfigured) return EMPTY;
  const { limit = 20, cursor, signal } = options;
  return apiGet<ProteinListResponse>("/proteins", {
    params: toParams(query.trim(), filters, limit, cursor),
    signal,
  });
}

export async function getProtein(
  accession: string,
  signal?: AbortSignal,
): Promise<ProteinSequence | null> {
  if (!isApiConfigured) return null;
  return apiGet<ProteinSequence>(`/proteins/${encodeURIComponent(accession)}`, { signal });
}
