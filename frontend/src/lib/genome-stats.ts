/** Derive /genomes headline counts from live API payloads — never hardcoded. */

export function deriveGenomeOverviewStats(
  listed: { organism: string }[],
  listTotal: number,
  stats: {
    genomes?: number;
    organisms?: number;
    genomeDistinctOrganisms?: number | null;
  } | null,
): {
  stored: number;
  distinctOrganisms: number;
  trackedOrganisms: number | null;
} {
  const stored =
    stats && typeof stats.genomes === "number" ? stats.genomes : listTotal;
  const fromPage = new Set(listed.map((row) => row.organism).filter(Boolean)).size;
  const distinct =
    stats && typeof stats.genomeDistinctOrganisms === "number"
      ? stats.genomeDistinctOrganisms
      : fromPage;
  return {
    stored,
    distinctOrganisms: distinct,
    trackedOrganisms: stats && typeof stats.organisms === "number" ? stats.organisms : null,
  };
}
