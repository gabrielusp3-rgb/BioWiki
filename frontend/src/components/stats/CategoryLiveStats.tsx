"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Skeleton, StatCard } from "@/components/ui";
import { LiveCountsUnavailable } from "@/components/stats/LiveCountsUnavailable";
import { fadeInUp, staggerContainer } from "@/lib/animations";
import { isApiConfigured } from "@/lib/api";
import type { CategoryKey } from "@/lib/design-tokens";
import { getStatistics } from "@/services/statisticsService";

export interface PageMetaStat {
  id: string;
  value: number;
  suffix?: string;
  label: string;
  testId?: string;
}

export function CategoryLiveStats({
  category,
  primaryKey,
  primaryId,
  primaryLabel,
  organismLabel,
}: {
  category: CategoryKey;
  /** `/statistics` category key for the live record count. */
  primaryKey: string;
  primaryId: string;
  primaryLabel: string;
  organismLabel: string;
}) {
  const [items, setItems] = useState<PageMetaStat[] | null>(null);
  const [unavailable, setUnavailable] = useState(!isApiConfigured);

  useEffect(() => {
    if (!isApiConfigured) return;
    const controller = new AbortController();
    getStatistics(controller.signal)
      .then((stats) => {
        if (controller.signal.aborted) return;
        if (!stats) {
          setUnavailable(true);
          return;
        }
        const categoryStats = stats.categories.find((c) => c.key === primaryKey);
        if (
          categoryStats === undefined ||
          typeof categoryStats.distinctOrganisms !== "number"
        ) {
          setUnavailable(true);
          return;
        }
        setUnavailable(false);
        setItems([
          {
            id: primaryId,
            value: categoryStats.count,
            label: primaryLabel,
            testId: `live-count-${primaryKey}`,
          },
          {
            id: "category-organisms",
            value: categoryStats.distinctOrganisms,
            label: organismLabel,
            testId: `live-count-${primaryKey}-organisms`,
          },
          {
            id: "organisms-tracked",
            value: stats.organisms,
            label: "Organisms tracked (database)",
            testId: "live-count-organisms-tracked",
          },
        ]);
      })
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        if (error instanceof DOMException && error.name === "AbortError") return;
        setUnavailable(true);
      });
    return () => controller.abort();
  }, [organismLabel, primaryId, primaryKey, primaryLabel]);

  if (unavailable) {
    return <LiveCountsUnavailable />;
  }

  return (
    <motion.div
      variants={staggerContainer(0.08, 0.04)}
      initial="hidden"
      animate="visible"
      className="grid grid-cols-1 gap-4 sm:grid-cols-3"
      data-testid="category-stat-cards"
    >
      {items === null
        ? Array.from({ length: 3 }, (_, i) => (
            <motion.div key={`sk-${i}`} variants={fadeInUp}>
              <Skeleton height={140} />
            </motion.div>
          ))
        : items.map((stat, i) => (
            <motion.div key={stat.id} variants={fadeInUp}>
              <StatCard
                value={stat.value}
                suffix={stat.suffix}
                label={stat.label}
                category={category}
                index={i + 1}
                testId={stat.testId}
              />
            </motion.div>
          ))}
    </motion.div>
  );
}
