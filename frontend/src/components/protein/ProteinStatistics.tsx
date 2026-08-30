"use client";

import { CategoryLiveStats } from "@/components/stats/CategoryLiveStats";

const PROTEIN_META_STATS = [
  { id: "sources", value: 3, label: "Public sources" },
  { id: "formats", value: 3, label: "Export formats" },
];

export function ProteinStatistics() {
  return (
    <CategoryLiveStats
      category="protein"
      primaryKey="protein"
      primaryId="proteins"
      primaryLabel="Proteins"
      extraStats={PROTEIN_META_STATS}
    />
  );
}
