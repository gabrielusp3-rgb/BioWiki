"use client";

import { useEffect, useRef, useState } from "react";
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
}

interface LiveStat extends PageMetaStat {}

export function CategoryLiveStats({
  category,
  primaryKey,
  primaryId,
  primaryLabel,
  extraStats,
}: {
  category: CategoryKey;
  /** `/statistics` category key for the live record count. */
  primaryKey: string;
  primaryId: string;
  primaryLabel: string;
  extraStats: PageMetaStat[];
}) {
  const extraRef = useRef(extraStats);
  extraRef.current = extraStats;
  const [items, setItems] = useState<LiveStat[] | null>(null);
  const [unavailable, setUnavailable] = useState(!isApiConfigured);

  useEffect(() => {
    if (!isApiConfigured) return;
    const controller = new AbortController();
    getStatistics(controller.signal)
      .then((stats) => {
        if (!stats || controller.signal.aborted) return;
        setItems([
          {
            id: primaryId,
            value: stats.categories.find((c) => c.key === primaryKey)?.count ?? 0,
            label: primaryLabel,
          },
          { id: "organisms", value: stats.organisms, label: "Organisms" },
          ...extraRef.current,
        ]);
      })
      .catch(() => {
        if (!controller.signal.aborted) setUnavailable(true);
      });
    return () => controller.abort();
  }, [primaryId, primaryKey, primaryLabel]);

  if (unavailable) {
    return (
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <LiveCountsUnavailable />
        <div className="grid grid-cols-2 gap-4">
          {extraStats.map((stat, i) => (
            <StatCard
              key={stat.id}
              value={stat.value}
              suffix={stat.suffix}
              label={stat.label}
              category={category}
              index={i + 1}
            />
          ))}
        </div>
      </div>
    );
  }

  const skeletonCount = 2 + extraStats.length;

  return (
    <motion.div
      variants={staggerContainer(0.08, 0.04)}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, amount: 0.3 }}
      className="grid grid-cols-2 gap-4 lg:grid-cols-4"
    >
      {items === null
        ? Array.from({ length: skeletonCount }, (_, i) => (
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
              />
            </motion.div>
          ))}
    </motion.div>
  );
}
