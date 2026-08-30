"use client";

import { CategoryLiveStats } from "@/components/stats/CategoryLiveStats";

const CRISPR_META_STATS = [
  { id: "systems", value: 4, label: "Cas systems" },
  { id: "formats", value: 3, label: "Export formats" },
];

export function CRISPRStatistics() {
  return (
    <CategoryLiveStats
      category="crispr"
      primaryKey="crispr"
      primaryId="crispr"
      primaryLabel="CRISPR records"
      extraStats={CRISPR_META_STATS}
    />
  );
}
