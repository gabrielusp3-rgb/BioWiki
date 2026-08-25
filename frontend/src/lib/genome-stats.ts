/** Derive /genomes headline counts from live API payloads — never hardcoded. */

export function deriveGenomeOverviewStats(
  listed: { organism: string }[],
  listTotal: number,
  stats: { genomes?: number; organisms?: number } | null,
): {
  stored: number;
  distinctOrganisms: number;
  trackedOrganisms: number;
} {
  const stored =
    stats && typeof stats.genomes === "number" ? stats.genomes : listTotal;
  return {
    stored,
    distinctOrganisms: new Set(listed.map((row) => row.organism).filter(Boolean)).size,
    trackedOrganisms: stats?.organisms ?? 0,
  };
}
