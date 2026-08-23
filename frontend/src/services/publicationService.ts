import { apiGet, ApiError, isApiConfigured } from "@/lib/api";
import type {
  Publication,
  PublicationDetail,
  PublicationListResponse,
} from "@/types/publication";

const EMPTY: PublicationListResponse = { results: [], total: 0, nextCursor: null };

/**
 * Publications data access, backed by `/publications`.
 * Records come from PubMed and source REFERENCE blocks — when the API is not
 * configured callers receive empty, honest results.
 */
export async function listPublications(
  options: {
    accession?: string;
    organism?: string;
    q?: string;
    limit?: number;
    cursor?: string;
    signal?: AbortSignal;
  } = {},
): Promise<PublicationListResponse> {
  if (!isApiConfigured) return EMPTY;
  const { accession, organism, q, limit = 20, cursor, signal } = options;
  return apiGet<PublicationListResponse>("/publications", {
    params: { accession, organism, q, limit, cursor },
    signal,
  });
}

export async function getPublication(
  pubmedId: number | string,
  signal?: AbortSignal,
): Promise<PublicationDetail | null> {
  if (!isApiConfigured) return null;
  try {
    return await apiGet<PublicationDetail>(
      `/publications/${encodeURIComponent(String(pubmedId))}`,
      { signal },
    );
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null;
    throw error;
  }
}

export function pubmedUrl(publication: Publication): string | null {
  if (publication.pubmedId) {
    return `https://pubmed.ncbi.nlm.nih.gov/${publication.pubmedId}/`;
  }
  return publication.url;
}
