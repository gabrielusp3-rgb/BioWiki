"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Container, Section, StatCard } from "@/components/ui";
import { SyncStatusBadge } from "@/components/sections/SyncStatusBadge";
import { fadeInUp, staggerContainer } from "@/lib/animations";
import { isApiConfigured } from "@/lib/api";
import { INSTITUTIONAL_STATISTICS, type Statistic } from "@/lib/statistics";
import { getStatistics, type SyncInfo } from "@/services/statisticsService";

export interface LiveStatisticsProps {
  /** Defaults to live database aggregates; institutional figures otherwise. */
  statistics?: Statistic[];
}

/**
 * When the backend is connected the section shows REAL aggregates from
 * `/statistics` — even small ones. The institutional capacity figures are only
 * shown while no database is configured, never on top of real counts.
 */
export function LiveStatistics({ statistics }: LiveStatisticsProps) {
  const [live, setLive] = useState<Statistic[] | null>(null);
  const [sync, setSync] = useState<SyncInfo | null>(null);

  useEffect(() => {
    if (statistics || !isApiConfigured) return;
    const controller = new AbortController();
    getStatistics(controller.signal)
      .then((stats) => {
        if (!stats || controller.signal.aborted) return;
        const byKey = Object.fromEntries(stats.categories.map((c) => [c.key, c.count]));
        setSync(stats.sync);
        setLive([
          { id: "sequences", value: stats.totalSequences, label: "Sequences" },
          { id: "organisms", value: stats.organisms, label: "Organisms" },
          { id: "proteins", value: byKey.protein ?? 0, label: "Proteins", category: "protein" },
          { id: "rna", value: byKey.rna ?? 0, label: "RNA", category: "rna" },
          { id: "dna", value: byKey.dna ?? 0, label: "DNA", category: "dna" },
          { id: "publications", value: stats.publications, label: "Publications" },
        ]);
      })
      .catch(() => {
        if (!controller.signal.aborted) setSync({ status: "offline", activeImports: 0, countsInSync: false, lastRun: null });
      });
    return () => controller.abort();
  }, [statistics]);

  const items = statistics ?? live ?? (isApiConfigured ? [] : INSTITUTIONAL_STATISTICS);
  const isLive = !statistics && live !== null;

  return (
    <Container width="wide">
      <Section
        eyebrow={isLive ? "Live Statistics · real-time aggregates" : "Live Statistics"}
        title="Scale of the Database"
        action={isApiConfigured && !statistics ? <SyncStatusBadge sync={sync} /> : undefined}
      >
        <motion.div
          variants={staggerContainer(0.08, 0.05)}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.2 }}
          className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3"
        >
          {items.map((stat, i) => (
            <motion.div key={stat.id} variants={fadeInUp}>
              <StatCard
                value={stat.value}
                suffix={stat.suffix}
                label={stat.label}
                category={stat.category}
                index={i + 1}
              />
            </motion.div>
          ))}
        </motion.div>
      </Section>
    </Container>
  );
}
