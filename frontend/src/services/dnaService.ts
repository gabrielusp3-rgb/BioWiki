import { apiGet, isApiConfigured } from "@/lib/api";
import type { DnaFilters, DnaListResponse, DnaSequence } from "@/types/dna";

/**
 * DNA data access.
 * Backed by the FastAPI `/sequences` endpoint (type=dna) over PostgreSQL.
 * When the API is not configured, callers receive empty, honest results — the
 * page never fabricates sequences.
 */
function toParams(query: string, filters: DnaFilters, limit: number, cursor?: string) {
  return {
    type: "dna",
    q: query || undefined,
    organism: filters.organism || undefined,
    source: filters.source !== "all" ? filters.source : undefined,
    molecule_type: filters.moleculeType !== "all" ? filters.moleculeType : undefined,
    strand: filters.strand !== "all" ? filters.strand : undefined,
    min_length: filters.minLength ?? undefined,
    max_length: filters.maxLength ?? undefined,
    limit,
    cursor,
  };
}

const EMPTY: DnaListResponse = { results: [], total: 0, nextCursor: null };

export async function listDna(
  query: string,
  filters: DnaFilters,
  options: { limit?: number; cursor?: string; signal?: AbortSignal } = {},
): Promise<DnaListResponse> {
  if (!isApiConfigured) return EMPTY;
  const { limit = 20, cursor, signal } = options;
  return apiGet<DnaListResponse>("/sequences", {
    params: toParams(query.trim(), filters, limit, cursor),
    signal,
  });
}

export async function getDna(
  accession: string,
  signal?: AbortSignal,
): Promise<DnaSequence | null> {
  if (!isApiConfigured) return null;
  return apiGet<DnaSequence>(`/sequences/${encodeURIComponent(accession)}`, { signal });
}
