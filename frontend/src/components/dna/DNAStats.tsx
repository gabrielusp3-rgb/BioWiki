"use client";

import { CategoryLiveStats } from "@/components/stats/CategoryLiveStats";

export function DNAStats() {
  return (
    <CategoryLiveStats
      category="dna"
      primaryKey="dna"
      primaryId="dna"
      primaryLabel="DNA sequences stored"
      organismLabel="Organisms with DNA-level data"
    />
  );
}
