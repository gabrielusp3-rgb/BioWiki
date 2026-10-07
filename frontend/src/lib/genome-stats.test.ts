import { describe, expect, it } from "vitest";
import { deriveGenomeOverviewStats } from "./genome-stats";

describe("deriveGenomeOverviewStats", () => {
  const listed = [
    { organism: "Fixture organism A" },
    { organism: "Fixture organism B" },
    { organism: "Fixture organism B" },
  ];

  it("prefers the statistics category distinct-organism count over the current page", () => {
    const stats = deriveGenomeOverviewStats(listed, 107, {
      genomes: 107,
      organisms: 1881,
      genomeDistinctOrganisms: 34,
    });
    expect(stats.stored).toBe(107);
    expect(stats.distinctOrganisms).toBe(34);
    expect(stats.trackedOrganisms).toBe(1881);
  });

  it("uses the live statistics total when assemblies exist", () => {
    const stats = deriveGenomeOverviewStats(listed, listed.length, {
      genomes: listed.length,
      organisms: 11,
    });
    expect(stats.stored).toBe(listed.length);
    expect(stats.distinctOrganisms).toBe(2);
    expect(stats.trackedOrganisms).toBe(11);
    expect(stats.stored).not.toBe(0);
  });

  it("falls back to the list total when statistics are unavailable", () => {
    const stats = deriveGenomeOverviewStats(listed, 3, null);
    expect(stats.stored).toBe(3);
    expect(stats.distinctOrganisms).toBe(2);
    expect(stats.trackedOrganisms).toBeNull();
  });
});
