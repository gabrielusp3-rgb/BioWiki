"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Skeleton, StatCard } from "@/components/ui";
import { fadeInUp, staggerContainer } from "@/lib/animations";
import { isApiConfigured } from "@/lib/api";
import { PROTEIN_PAGE_STATS } from "@/lib/protein";
import { getStatistics } from "@/services/statisticsService";

export function ProteinStatistics() {
  const [items, setItems] = useState(isApiConfigured ? null : PROTEIN_PAGE_STATS);

  useEffect(() => {
    if (!isApiConfigured) return;
    const controller = new AbortController();
    getStatistics(controller.signal)
      .then((stats) => {
        if (!stats || controller.signal.aborted) return;
        const protein = stats.categories.find((c) => c.key === "protein")?.count ?? 0;
        setItems([
          { id: "proteins", value: protein, label: "Proteins" },
          { id: "organisms", value: stats.organisms, label: "Organisms" },
          PROTEIN_PAGE_STATS[2],
          PROTEIN_PAGE_STATS[3],
        ]);
      })
      .catch(() => {
        if (!controller.signal.aborted) setItems(PROTEIN_PAGE_STATS);
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
      {(items ?? PROTEIN_PAGE_STATS).map((stat, i) => (
        <motion.div key={stat.id} variants={fadeInUp}>
          {items === null ? (
            <Skeleton height={140} />
          ) : (
            <StatCard
              value={stat.value}
              suffix={stat.suffix}
              label={stat.label}
              category="protein"
              index={i + 1}
            />
          )}
        </motion.div>
      ))}
    </motion.div>
  );
}
