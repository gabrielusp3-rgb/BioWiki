"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  Badge,
  Card,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
  Container,
  Section,
  Skeleton,
} from "@/components/ui";
import { ChevronRightIcon } from "@/components/ui/Icons";
import { fadeInUp, staggerContainer } from "@/lib/animations";
import { isApiConfigured } from "@/lib/api";
import { CATEGORY_CARDS, type CategoryCardData } from "@/lib/category-cards";
import { CATEGORY_META } from "@/lib/categories";
import { formatStatistic } from "@/lib/statistics";
import { getStatistics } from "@/services/statisticsService";
import { getPaleogenomicsStatistics } from "@/services/paleogenomicsService";

function CategoryCard({
  data,
  liveCount,
  awaitingLive,
  unavailable,
}: {
  data: CategoryCardData;
  liveCount?: number;
  awaitingLive?: boolean;
  unavailable?: boolean;
}) {
  const meta = CATEGORY_META[data.key];
  const { Icon } = data;

  return (
    <motion.div variants={fadeInUp} className="h-full">
      <Link href={data.href} className="block h-full">
        <Card category={data.key} interactive className="group h-full">
          <CardHeader>
            <span
              className="grid h-12 w-12 place-items-center border transition-all duration-300"
              style={{
                color: meta.color,
                borderColor: `${meta.color}59`,
                backgroundColor: `${meta.color}14`,
                boxShadow: meta.glow,
              }}
            >
              <Icon className="h-6 w-6" />
            </span>
            <Badge category={data.key} />
          </CardHeader>

          <CardTitle className="mb-3" style={{ color: meta.color }}>
            {data.label}
          </CardTitle>
          <CardDescription>{data.description}</CardDescription>

          <CardFooter>
            <span className="flex flex-col">
              {awaitingLive ? (
                <Skeleton width={96} height={28} />
              ) : unavailable || liveCount === undefined ? (
                <span className="font-display text-sm font-semibold uppercase tracking-wide text-content-muted">
                  Unavailable
                </span>
              ) : (
                <span className="font-display text-2xl font-bold tracking-tightest tabular-nums text-content-primary">
                  {formatStatistic(liveCount)}
                </span>
              )}
              <span className="text-[11px] uppercase tracking-wider text-content-muted">
                Records
              </span>
            </span>
            <span
              className="flex items-center gap-1 text-xs font-semibold uppercase tracking-wide transition-transform duration-300 group-hover:translate-x-1"
              style={{ color: meta.color }}
            >
              Explore
              <ChevronRightIcon className="h-4 w-4" />
            </span>
          </CardFooter>
        </Card>
      </Link>
    </motion.div>
  );
}

function PaleogenomicsHomeLink() {
  const [species, setSpecies] = useState<number | null>(null);
  const [sequences, setSequences] = useState<number | null>(null);

  useEffect(() => {
    if (!isApiConfigured) return;
    const controller = new AbortController();
    getPaleogenomicsStatistics(controller.signal)
      .then((stats) => {
        if (!stats || controller.signal.aborted) return;
        setSpecies(stats.speciesCount);
        setSequences(stats.sequenceCount);
      })
      .catch(() => {
        /* keep the collection entry even if counts are unreachable */
      });
    return () => controller.abort();
  }, []);

  return (
    <Link
      href="/paleogenomics"
      className="glass hairline mt-4 flex flex-col gap-3 p-6 transition-colors hover:border-white/20 sm:flex-row sm:items-center sm:justify-between"
    >
      <div>
        <p className="eyebrow mb-2">Collection</p>
        <p className="font-display text-xl font-semibold text-content-primary">Paleogenomics</p>
        <p className="mt-2 max-w-2xl text-sm text-content-secondary">
          Extinct species, ancient DNA, archaic hominins, and introgression in living humans —
          authentic records inside this catalogue, not a second product.
        </p>
      </div>
      <div className="flex shrink-0 gap-8 font-mono text-xs text-content-muted">
        <span>
          {species === null ? "—" : formatStatistic(species)} species
        </span>
        <span>
          {sequences === null ? "—" : formatStatistic(sequences)} sequences
        </span>
      </div>
    </Link>
  );
}

export function Categories() {
  const [liveCounts, setLiveCounts] = useState<Record<string, number> | null>(null);
  const [unavailable, setUnavailable] = useState(!isApiConfigured);

  useEffect(() => {
    if (!isApiConfigured) return;
    const controller = new AbortController();
    getStatistics(controller.signal)
      .then((stats) => {
        if (!stats || controller.signal.aborted) return;
        setLiveCounts(
          Object.fromEntries(stats.categories.map((c) => [c.key, c.count])),
        );
        setUnavailable(false);
      })
      .catch(() => {
        if (!controller.signal.aborted) setUnavailable(true);
      });
    return () => controller.abort();
  }, []);

  return (
    <Container width="wide">
      <Section
        eyebrow="Categories"
        title="Explore by biological category"
        description="Six curated domains, each backed by real sequences from internationally recognised public databases."
      >
        <motion.div
          variants={staggerContainer(0.08, 0.05)}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.15 }}
          className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3"
        >
          {CATEGORY_CARDS.map((data) => (
            <CategoryCard
              key={data.key}
              data={data}
              liveCount={liveCounts == null ? undefined : (liveCounts[data.key] ?? 0)}
              awaitingLive={isApiConfigured && liveCounts === null && !unavailable}
              unavailable={unavailable}
            />
          ))}
        </motion.div>
        <PaleogenomicsHomeLink />
      </Section>
    </Container>
  );
}
