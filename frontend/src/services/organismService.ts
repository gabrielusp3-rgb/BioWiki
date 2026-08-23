import { apiGet, ApiError, isApiConfigured } from "@/lib/api";
import { ncbiTaxonomyUrl, REFERENCE_ORGANISMS } from "@/lib/organisms";
import type { Organism } from "@/types/organism";

interface OrganismListResponse {
  organisms: Organism[];
  total: number;
}

/**
 * The backend serves the canonical organism record (slug, taxId, lineage…)
 * but not UI navigation links. Derive them here from the real identifiers —
 * nothing is invented, both URLs resolve to verifiable resources.
 */
function normalizeOrganism(raw: Organism): Organism {
  return {
    ...raw,
    lineage: raw.lineage ?? [],
    links: raw.links ?? [
      { label: "View organism", url: `/organisms/${raw.slug}` },
      { label: "NCBI Taxonomy", url: ncbiTaxonomyUrl(raw.taxId), external: true },
    ],
  };
}

/**
 * Featured organisms.
 * When the backend is connected, real records (with real sequence counts) are
 * returned from `/organisms/featured`. Otherwise we fall back to the reference
 * identities, whose counts stay `null` — the UI never fabricates totals.
 */
export async function getFeaturedOrganisms(
  limit = 12,
  signal?: AbortSignal,
): Promise<Organism[]> {
  if (!isApiConfigured) {
    return REFERENCE_ORGANISMS.slice(0, limit);
  }

  const response = await apiGet<OrganismListResponse>("/organisms/featured", {
    params: { limit },
    signal,
  });
  const organisms = response.organisms.map(normalizeOrganism);
  // Honest fallback: an empty database shows the reference identities
  // (real NCBI taxa with null counts) instead of a blank section.
  return organisms.length > 0 ? organisms : REFERENCE_ORGANISMS.slice(0, limit);
}

/** Paginated organism listing — prepared for hundreds of organisms. */
export async function listOrganisms(
  options: { limit?: number; cursor?: string; group?: string; signal?: AbortSignal } = {},
): Promise<OrganismListResponse> {
  const { limit = 60, cursor, group, signal } = options;
  if (!isApiConfigured) {
    return { organisms: REFERENCE_ORGANISMS, total: REFERENCE_ORGANISMS.length };
  }
  const response = await apiGet<OrganismListResponse>("/organisms", {
    params: { limit, cursor, group },
    signal,
  });
  return { ...response, organisms: response.organisms.map(normalizeOrganism) };
}

/**
 * Organism detail by slug, NCBI tax ID or internal ID.
 * Falls back to the reference identities (matched by slug/taxId) when the API
 * is not configured; returns `null` when the record does not exist.
 */
export async function getOrganism(
  identifier: string,
  signal?: AbortSignal,
): Promise<Organism | null> {
  if (!isApiConfigured) {
    return (
      REFERENCE_ORGANISMS.find(
        (o) => o.slug === identifier || String(o.taxId) === identifier,
      ) ?? null
    );
  }
  try {
    const raw = await apiGet<Organism>(
      `/organisms/${encodeURIComponent(identifier)}`,
      { signal },
    );
    return normalizeOrganism(raw);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null;
    throw error;
  }
}
