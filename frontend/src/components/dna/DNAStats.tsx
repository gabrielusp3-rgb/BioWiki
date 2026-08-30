"use client";

import { CategoryLiveStats } from "@/components/stats/CategoryLiveStats";

const DNA_META_STATS = [
  { id: "sources", value: 5, label: "Public sources" },
  { id: "formats", value: 3, label: "Export formats" },
];

export function DNAStats() {
  return (
    <CategoryLiveStats
      category="dna"
      primaryKey="dna"
      primaryId="dna"
      primaryLabel="DNA sequences"
      extraStats={DNA_META_STATS}
    />
  );
}
