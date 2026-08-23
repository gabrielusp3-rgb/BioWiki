import { apiGet, isApiConfigured } from "@/lib/api";
import type { CrisprFilters, CrisprGuide, CrisprListResponse } from "@/types/crispr";

/**
 * CRISPR guide data access.
 * Backed by the FastAPI `/sequences` endpoint (type=crispr) over PostgreSQL.
 * Returns empty, honest results when the API is not configured — no guides,
 * scores or targets are fabricated on the client.
 */
function toParams(query: string, filters: CrisprFilters, limit: number, cursor?: string) {
  return {
    type: "crispr",
    q: query || undefined,
    organism: filters.organism || undefined,
    source: filters.source !== "all" ? filters.source : undefined,
    system: filters.system !== "all" ? filters.system : undefined,
    target_gene: filters.targetGene || undefined,
    pam: filters.pam || undefined,
    min_length: filters.minLength ?? undefined,
    max_length: filters.maxLength ?? undefined,
    limit,
    cursor,
  };
}

const EMPTY: CrisprListResponse = { results: [], total: 0, nextCursor: null };

export async function listCrispr(
  query: string,
  filters: CrisprFilters,
  options: { limit?: number; cursor?: string; signal?: AbortSignal } = {},
): Promise<CrisprListResponse> {
  if (!isApiConfigured) return EMPTY;
  const { limit = 20, cursor, signal } = options;
  return apiGet<CrisprListResponse>("/sequences", {
    params: toParams(query.trim(), filters, limit, cursor),
    signal,
  });
}

export async function getCrispr(
  accession: string,
  signal?: AbortSignal,
): Promise<CrisprGuide | null> {
  if (!isApiConfigured) return null;
  return apiGet<CrisprGuide>(`/sequences/${encodeURIComponent(accession)}`, { signal });
}
