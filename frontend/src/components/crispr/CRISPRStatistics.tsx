"use client";

import { CategoryLiveStats } from "@/components/stats/CategoryLiveStats";

export function CRISPRStatistics() {
  return (
    <CategoryLiveStats
      category="crispr"
      primaryKey="crispr"
      primaryId="crispr"
      primaryLabel="CRISPR records stored"
      organismLabel="Organisms with CRISPR-level data"
    />
  );
}
