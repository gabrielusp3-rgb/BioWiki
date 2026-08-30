"use client";

import { CategoryLiveStats } from "@/components/stats/CategoryLiveStats";

const RNA_META_STATS = [
  { id: "classes", value: 6, label: "RNA classes" },
  { id: "formats", value: 3, label: "Export formats" },
];

export function RNAStats() {
  return (
    <CategoryLiveStats
      category="rna"
      primaryKey="rna"
      primaryId="rna"
      primaryLabel="RNA sequences"
      extraStats={RNA_META_STATS}
    />
  );
}
