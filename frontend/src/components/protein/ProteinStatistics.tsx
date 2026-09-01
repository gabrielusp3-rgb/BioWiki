"use client";

import { CategoryLiveStats } from "@/components/stats/CategoryLiveStats";

export function ProteinStatistics() {
  return (
    <CategoryLiveStats
      category="protein"
      primaryKey="protein"
      primaryId="proteins"
      primaryLabel="Proteins stored"
      organismLabel="Organisms with protein-level data"
    />
  );
}
