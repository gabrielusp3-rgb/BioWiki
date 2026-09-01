"use client";

import { CategoryLiveStats } from "@/components/stats/CategoryLiveStats";

export function RNAStats() {
  return (
    <CategoryLiveStats
      category="rna"
      primaryKey="rna"
      primaryId="rna"
      primaryLabel="RNA sequences stored"
      organismLabel="Organisms with RNA-level data"
    />
  );
}
