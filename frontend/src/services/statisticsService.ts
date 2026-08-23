import { apiGet, isApiConfigured } from "@/lib/api";

export interface CategoryStat {
  key: string;
  label: string;
  count: number;
  totalResidues: number;
}

export type SyncStatus =
  | "empty"
  | "importing"
  | "error"
  | "updated"
  | "connected"
  | "offline";

export interface LastRun {
  sourceKey: string;
  kind: string;
  status: string;
  finishedAt: string | null;
  created: number | null;
  updated: number | null;
  failed: number | null;
}

export interface SyncInfo {
  status: SyncStatus;
  activeImports: number;
  countsInSync: boolean;
  lastRun: LastRun | null;
}

export interface DatabaseStatistics {
  totalSequences: number;
  totalResidues: number;
  organisms: number;
  genes: number;
  genomes: number;
  publications: number;
  linkedPublications: number;
  categories: CategoryStat[];
  sync: SyncInfo;
  lastUpdated: string | null;
}

export interface IntegrityCheck {
  name: string;
  ok: boolean;
  detail: string;
  expected: number | null;
  actual: number | null;
}

export interface IntegrityReport {
  ok: boolean;
  checkedAt: string;
  checks: IntegrityCheck[];
}

/**
 * Live aggregates from `/statistics` — every figure is computed from the real
 * database. Returns `null` when the API is not configured so the UI can show
 * its capacity figures instead of pretending to know live counts.
 */
let statisticsInflight: Promise<DatabaseStatistics | null> | null = null;
let statisticsCache: { at: number; data: DatabaseStatistics | null } | null = null;
const STATISTICS_TTL_MS = 15_000;

export async function getStatistics(
  signal?: AbortSignal,
): Promise<DatabaseStatistics | null> {
  if (!isApiConfigured) return null;
  if (signal?.aborted) {
    throw new DOMException("The operation was aborted.", "AbortError");
  }
  const now = Date.now();
  if (statisticsCache && now - statisticsCache.at < STATISTICS_TTL_MS) {
    return statisticsCache.data;
  }
  // Coalesce concurrent callers (home LiveStatistics + Categories) onto one
  // request. The network fetch is not tied to any one AbortSignal so a
  // Strict-Mode remount cannot cancel a sibling still waiting for the same data.
  if (!statisticsInflight) {
    statisticsInflight = apiGet<DatabaseStatistics>("/statistics").finally(() => {
      statisticsInflight = null;
    });
  }
  const data = await statisticsInflight;
  statisticsCache = { at: Date.now(), data };
  if (signal?.aborted) {
    throw new DOMException("The operation was aborted.", "AbortError");
  }
  return data;
}

export async function getIntegrity(
  signal?: AbortSignal,
): Promise<IntegrityReport | null> {
  if (!isApiConfigured) return null;
  return apiGet<IntegrityReport>("/statistics/integrity", { signal });
}
