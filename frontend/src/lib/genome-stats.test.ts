import { describe, expect, it } from "vitest";
import { deriveGenomeOverviewStats } from "./genome-stats";

describe("deriveGenomeOverviewStats", () => {
  const listed = [
    { organism: "Fixture organism A" },
    { organism: "Fixture organism B" },
    { organism: "Fixture organism B" },
  ];

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
    expect(stats.trackedOrganisms).toBe(0);
  });
});
