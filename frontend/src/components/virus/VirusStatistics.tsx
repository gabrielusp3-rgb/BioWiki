"use client";

import { CategoryLiveStats } from "@/components/stats/CategoryLiveStats";

export function VirusStatistics() {
  return (
    <CategoryLiveStats
      category="virus"
      primaryKey="virus"
      primaryId="virus"
      primaryLabel="Viral sequences stored"
      organismLabel="Organisms with viral sequence data"
    />
  );
}
