"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Container, Section, Skeleton, StatCard } from "@/components/ui";
import { LiveCountsUnavailable } from "@/components/stats/LiveCountsUnavailable";
import { SyncStatusBadge } from "@/components/sections/SyncStatusBadge";
import { fadeInUp, staggerContainer } from "@/lib/animations";
import { isApiConfigured } from "@/lib/api";
import type { Statistic } from "@/lib/statistics";
import { getStatistics, type SyncInfo } from "@/services/statisticsService";

export interface LiveStatisticsProps {
  /** Optional preloaded live aggregates. Never pass fabricated scale figures. */
  statistics?: Statistic[];
}

/**
 * Real aggregates from `/statistics`. When the API is unreachable the section
 * states that counts are unavailable instead of inventing catalogue scale.
 */
export function LiveStatistics({ statistics }: LiveStatisticsProps) {
  const [live, setLive] = useState<Statistic[] | null>(statistics ?? null);
  const [sync, setSync] = useState<SyncInfo | null>(null);
  const [unavailable, setUnavailable] = useState(!statistics && !isApiConfigured);

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
          { id: "dna", value: byKey.dna ?? 0, label: "DNA", category: "dna" },
          { id: "rna", value: byKey.rna ?? 0, label: "RNA", category: "rna" },
          { id: "proteins", value: byKey.protein ?? 0, label: "Proteins", category: "protein" },
          { id: "crispr", value: byKey.crispr ?? 0, label: "CRISPR", category: "crispr" },
          { id: "virus", value: byKey.virus ?? 0, label: "Virus", category: "virus" },
          { id: "publications", value: stats.publications, label: "Publications" },
          { id: "organisms", value: stats.organisms, label: "Organisms" },
          { id: "genomes", value: stats.genomes, label: "Genome assemblies", category: "genome" },
        ]);
      })
      .catch(() => {
        if (!controller.signal.aborted) {
          setUnavailable(true);
          setSync({ status: "offline", activeImports: 0, countsInSync: false, lastRun: null });
        }
      });
    return () => controller.abort();
  }, [statistics]);

  const isLive = !statistics && live !== null && !unavailable;

  return (
    <Container width="wide">
      <Section
        eyebrow={isLive ? "Live Statistics · real-time aggregates" : "Live Statistics"}
        title="Scale of the Database"
        action={isApiConfigured && !statistics ? <SyncStatusBadge sync={sync} /> : undefined}
      >
        {unavailable ? (
          <LiveCountsUnavailable />
        ) : live === null ? (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 9 }, (_, i) => (
              <Skeleton key={i} height={140} />
            ))}
          </div>
        ) : (
          <motion.div
            variants={staggerContainer(0.08, 0.05)}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.2 }}
            className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3"
          >
            {live.map((stat, i) => (
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
        )}
      </Section>
    </Container>
  );
}
