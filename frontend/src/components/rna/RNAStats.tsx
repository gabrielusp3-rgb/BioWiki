"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Skeleton, StatCard } from "@/components/ui";
import { fadeInUp, staggerContainer } from "@/lib/animations";
import { isApiConfigured } from "@/lib/api";
import { RNA_PAGE_STATS } from "@/lib/rna";
import { getStatistics } from "@/services/statisticsService";

export function RNAStats() {
  const [items, setItems] = useState(isApiConfigured ? null : RNA_PAGE_STATS);

  useEffect(() => {
    if (!isApiConfigured) return;
    const controller = new AbortController();
    getStatistics(controller.signal)
      .then((stats) => {
        if (!stats || controller.signal.aborted) return;
        const rna = stats.categories.find((c) => c.key === "rna")?.count ?? 0;
        setItems([
          { id: "rna", value: rna, label: "RNA sequences" },
          { id: "organisms", value: stats.organisms, label: "Organisms" },
          RNA_PAGE_STATS[2],
          RNA_PAGE_STATS[3],
        ]);
      })
      .catch(() => {
        if (!controller.signal.aborted) setItems(RNA_PAGE_STATS);
      });
    return () => controller.abort();
  }, []);

  return (
    <motion.div
      variants={staggerContainer(0.08, 0.04)}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, amount: 0.3 }}
      className="grid grid-cols-2 gap-4 lg:grid-cols-4"
    >
      {(items ?? RNA_PAGE_STATS).map((stat, i) => (
        <motion.div key={stat.id} variants={fadeInUp}>
          {items === null ? (
            <Skeleton height={140} />
          ) : (
            <StatCard
              value={stat.value}
              suffix={stat.suffix}
              label={stat.label}
              category="rna"
              index={i + 1}
            />
          )}
        </motion.div>
      ))}
    </motion.div>
  );
}
