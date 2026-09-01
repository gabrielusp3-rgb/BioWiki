"use client";

import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { Skeleton, StatCard } from "@/components/ui";
import { LiveCountsUnavailable } from "@/components/stats/LiveCountsUnavailable";
import { fadeInUp, staggerContainer } from "@/lib/animations";
import { isApiConfigured } from "@/lib/api";
import type { CategoryKey } from "@/lib/design-tokens";
import { formatStatistic } from "@/lib/statistics";
import { getStatistics } from "@/services/statisticsService";

export interface PageMetaStat {
  id: string;
  value: number;
  suffix?: string;
  label: string;
}

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
        const liveCount = stats.categories.find((c) => c.key === primaryKey)?.count;
        if (liveCount === undefined) {
          setUnavailable(true);
          return;
        }
        setUnavailable(false);
        setItems([
          {
            id: primaryId,
            value: liveCount,
            label: primaryLabel,
          },
          { id: "organisms", value: stats.organisms, label: "Organisms" },
          ...extraRef.current,
        ]);
      })
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        if (error instanceof DOMException && error.name === "AbortError") return;
        setUnavailable(true);
      });
    return () => controller.abort();
  }, [primaryId, primaryKey, primaryLabel]);

  const primary = items?.[0];

  return (
    <div className="flex flex-col gap-6">
      {unavailable ? (
        <LiveCountsUnavailable />
      ) : primary == null ? (
        <Skeleton height={56} width={320} />
      ) : (
        <p
          data-testid={`live-count-${primaryKey}`}
          className="font-display text-4xl font-bold tracking-tightest tabular-nums text-content-primary sm:text-5xl"
        >
          {formatStatistic(primary.value)}{" "}
          <span className="font-display text-base font-semibold uppercase tracking-wide text-content-secondary sm:text-lg">
            {primaryLabel}
          </span>
        </p>
      )}

      {unavailable ? (
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
      ) : (
        <motion.div
          variants={staggerContainer(0.08, 0.04)}
          initial="hidden"
          animate="visible"
          className="grid grid-cols-2 gap-4 lg:grid-cols-4"
        >
          {items === null
            ? Array.from({ length: 2 + extraStats.length }, (_, i) => (
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
      )}
    </div>
  );
}
