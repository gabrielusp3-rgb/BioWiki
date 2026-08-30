"use client";

import { CategoryLiveStats } from "@/components/stats/CategoryLiveStats";

const VIRUS_META_STATS = [
  { id: "sources", value: 4, label: "Public sources" },
  { id: "formats", value: 3, label: "Export formats" },
];

export function VirusStatistics() {
  return (
    <CategoryLiveStats
      category="virus"
      primaryKey="virus"
      primaryId="virus"
      primaryLabel="Viral sequences"
      extraStats={VIRUS_META_STATS}
    />
  );
}
