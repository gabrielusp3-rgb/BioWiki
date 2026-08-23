"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Skeleton, StatCard } from "@/components/ui";
import { fadeInUp, staggerContainer } from "@/lib/animations";
import { isApiConfigured } from "@/lib/api";
import { VIRUS_PAGE_STATS } from "@/lib/virus";
import { getStatistics } from "@/services/statisticsService";

export function VirusStatistics() {
  const [items, setItems] = useState(isApiConfigured ? null : VIRUS_PAGE_STATS);

  useEffect(() => {
    if (!isApiConfigured) return;
    const controller = new AbortController();
    getStatistics(controller.signal)
      .then((stats) => {
        if (!stats || controller.signal.aborted) return;
        const virus = stats.categories.find((c) => c.key === "virus")?.count ?? 0;
        setItems([
          { id: "virus", value: virus, label: "Viral sequences" },
          { id: "organisms", value: stats.organisms, label: "Organisms" },
          VIRUS_PAGE_STATS[2],
          VIRUS_PAGE_STATS[3],
        ]);
      })
      .catch(() => {
        if (!controller.signal.aborted) setItems(VIRUS_PAGE_STATS);
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
      {(items ?? VIRUS_PAGE_STATS).map((stat, i) => (
        <motion.div key={stat.id} variants={fadeInUp}>
          {items === null ? (
            <Skeleton height={140} />
          ) : (
            <StatCard
              value={stat.value}
              suffix={stat.suffix}
              label={stat.label}
              category="virus"
              index={i + 1}
            />
          )}
        </motion.div>
      ))}
    </motion.div>
  );
}
