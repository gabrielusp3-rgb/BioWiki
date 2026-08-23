import { apiGet, isApiConfigured } from "@/lib/api";
import type { VirusFilters, VirusListResponse, VirusSequence } from "@/types/virus";

/**
 * Virus data access.
 * Backed by the FastAPI `/viruses` endpoint over PostgreSQL. Returns empty,
 * honest results when the API is not configured — no records are fabricated.
 */
function toParams(query: string, filters: VirusFilters, limit: number, cursor?: string) {
  return {
    q: query || undefined,
    family: filters.family || undefined,
    host: filters.host || undefined,
    source: filters.source !== "all" ? filters.source : undefined,
    genome_type: filters.genomeType !== "all" ? filters.genomeType : undefined,
    min_length: filters.minLength ?? undefined,
    max_length: filters.maxLength ?? undefined,
    limit,
    cursor,
  };
}

const EMPTY: VirusListResponse = { results: [], total: 0, nextCursor: null };

export async function listVirus(
  query: string,
  filters: VirusFilters,
  options: { limit?: number; cursor?: string; signal?: AbortSignal } = {},
): Promise<VirusListResponse> {
  if (!isApiConfigured) return EMPTY;
  const { limit = 20, cursor, signal } = options;
  return apiGet<VirusListResponse>("/viruses", {
    params: toParams(query.trim(), filters, limit, cursor),
    signal,
  });
}

export async function getVirus(
  accession: string,
  signal?: AbortSignal,
): Promise<VirusSequence | null> {
  if (!isApiConfigured) return null;
  return apiGet<VirusSequence>(`/viruses/${encodeURIComponent(accession)}`, { signal });
}
