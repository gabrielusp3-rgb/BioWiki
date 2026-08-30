import { apiGet, ApiError, isApiConfigured } from "@/lib/api";
import type { PublicationListResponse } from "@/types/publication";
import type { GenomeAssembly } from "@/types/sequence";
import type {
  PaleogenomicIntrogressionList,
  PaleogenomicLanding,
  PaleogenomicOverview,
  PaleogenomicProjectList,
  PaleogenomicSequenceList,
  PaleogenomicSpeciesDetail,
  PaleogenomicSpeciesList,
  PaleogenomicsListFilters,
} from "@/types/paleogenomics";

export async function getPaleogenomicsLanding(
  signal?: AbortSignal,
): Promise<PaleogenomicLanding | null> {
  if (!isApiConfigured) return null;
  return apiGet<PaleogenomicLanding>("/paleogenomics", { signal });
}

export async function getPaleogenomicsStatistics(
  signal?: AbortSignal,
): Promise<PaleogenomicOverview | null> {
  if (!isApiConfigured) return null;
  return apiGet<PaleogenomicOverview>("/paleogenomics/statistics", { signal });
}

export async function listPaleogenomicsSpecies(
  filters: PaleogenomicsListFilters & { limit?: number; cursor?: string; signal?: AbortSignal } = {},
): Promise<PaleogenomicSpeciesList> {
  const { signal, limit = 20, cursor, ...rest } = filters;
  if (!isApiConfigured) {
    return { results: [], total: 0, nextCursor: null };
  }
  return apiGet<PaleogenomicSpeciesList>("/paleogenomics/species", {
    signal,
    params: {
      q: rest.q,
      subsection: rest.subsection,
      extinction_status: rest.extinctionStatus,
      geographic_region: rest.geographicRegion,
      deextinction: rest.deextinction,
      dna_available: rest.dnaAvailable,
      assembly_available: rest.assemblyAvailable,
      limit,
      cursor,
    },
  });
}

export async function getPaleogenomicsSpecies(
  slug: string,
  signal?: AbortSignal,
): Promise<PaleogenomicSpeciesDetail | null> {
  if (!isApiConfigured) return null;
  try {
    return await apiGet<PaleogenomicSpeciesDetail>(
      `/paleogenomics/species/${encodeURIComponent(slug)}`,
      { signal },
    );
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null;
    throw error;
  }
}

export async function listPaleogenomicsSequences(
  slug: string,
  options: { limit?: number; cursor?: string; signal?: AbortSignal } = {},
): Promise<PaleogenomicSequenceList> {
  const { limit = 20, cursor, signal } = options;
  return apiGet<PaleogenomicSequenceList>(
    `/paleogenomics/species/${encodeURIComponent(slug)}/sequences`,
    { params: { limit, cursor }, signal },
  );
}

export async function listPaleogenomicsPublications(
  slug: string,
  options: { limit?: number; cursor?: string; signal?: AbortSignal } = {},
): Promise<PublicationListResponse> {
  const { limit = 20, cursor, signal } = options;
  return apiGet<PublicationListResponse>(
    `/paleogenomics/species/${encodeURIComponent(slug)}/publications`,
    { params: { limit, cursor }, signal },
  );
}

export async function listPaleogenomicsGenomes(
  slug: string,
  options: { limit?: number; cursor?: string; signal?: AbortSignal } = {},
): Promise<{ results: GenomeAssembly[]; total: number; nextCursor: string | null }> {
  const { limit = 20, cursor, signal } = options;
  return apiGet(
    `/paleogenomics/species/${encodeURIComponent(slug)}/genomes`,
    { params: { limit, cursor }, signal },
  );
}

export async function listPaleogenomicsProjects(
  slug: string,
  options: { limit?: number; cursor?: string; signal?: AbortSignal } = {},
): Promise<PaleogenomicProjectList> {
  const { limit = 20, cursor, signal } = options;
  return apiGet<PaleogenomicProjectList>(
    `/paleogenomics/species/${encodeURIComponent(slug)}/projects`,
    { params: { limit, cursor }, signal },
  );
}

export async function listIntrogression(
  options: { archaicSource?: string; limit?: number; cursor?: string; signal?: AbortSignal } = {},
): Promise<PaleogenomicIntrogressionList> {
  const { archaicSource, limit = 20, cursor, signal } = options;
  if (!isApiConfigured) {
    return {
      results: [],
      total: 0,
      nextCursor: null,
      note: "Introgression records appear once the sequence database is connected.",
    };
  }
  return apiGet<PaleogenomicIntrogressionList>("/paleogenomics/introgression", {
    params: { archaic_source: archaicSource, limit, cursor },
    signal,
  });
}
