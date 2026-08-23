import { API_BASE_URL, apiGet, ApiError, isApiConfigured } from "@/lib/api";
import type {
  GenomeAssembly,
  GenomeListResponse,
  SequenceDetail,
  SequenceSummaryListResponse,
} from "@/types/sequence";

/**
 * Category-agnostic sequence access used by the detail and organism pages.
 * All content comes from the database (`/sequences/{accession}` et al.);
 * a missing record yields `null`, never a fabricated fallback.
 */
export async function getSequence(
  accession: string,
  signal?: AbortSignal,
): Promise<SequenceDetail | null> {
  if (!isApiConfigured) return null;
  try {
    return await apiGet<SequenceDetail>(
      `/sequences/${encodeURIComponent(accession)}`,
      { signal },
    );
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null;
    throw error;
  }
}

const EMPTY_LIST: SequenceSummaryListResponse = { results: [], total: 0, nextCursor: null };

/** List sequences of one category for an organism (organism detail page). */
export async function listByOrganism(
  category: "dna" | "rna" | "crispr" | "protein" | "virus",
  organism: string,
  options: { limit?: number; signal?: AbortSignal } = {},
): Promise<SequenceSummaryListResponse> {
  if (!isApiConfigured) return EMPTY_LIST;
  const { limit = 6, signal } = options;
  const path =
    category === "protein" ? "/proteins" : category === "virus" ? "/viruses" : "/sequences";
  const params: Record<string, string | number> = { organism, limit };
  if (path === "/sequences") params.type = category;
  return apiGet<SequenceSummaryListResponse>(path, { params, signal });
}

export async function listGenomes(
  options: { organism?: string; limit?: number; signal?: AbortSignal } = {},
): Promise<GenomeListResponse> {
  if (!isApiConfigured) return { results: [], total: 0, nextCursor: null };
  const { organism, limit = 12, signal } = options;
  return apiGet<GenomeListResponse>("/genomes", { params: { organism, limit }, signal });
}

export async function getGenome(
  accession: string,
  signal?: AbortSignal,
): Promise<GenomeAssembly | null> {
  if (!isApiConfigured) return null;
  try {
    return await apiGet<GenomeAssembly>(
      `/genomes/${encodeURIComponent(accession)}`,
      { signal },
    );
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null;
    throw error;
  }
}

/** Backend export URL for one record (FASTA/GenBank/CSV/JSON downloads). */
export function sequenceDownloadUrl(
  accession: string,
  format: "fasta" | "genbank" | "csv" | "json",
): string {
  return `${API_BASE_URL}/download/sequence/${encodeURIComponent(accession)}?format=${format}`;
}
