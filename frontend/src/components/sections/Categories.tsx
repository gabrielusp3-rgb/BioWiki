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

function CategoryCard({
  data,
  liveCount,
  awaitingLive,
}: {
  data: CategoryCardData;
  /** Real database count; undefined while the API is not configured. */
  liveCount?: number;
  awaitingLive?: boolean;
}) {
  const meta = CATEGORY_META[data.key];
  const { Icon } = data;
  const count = liveCount ?? data.count;
  const suffix = liveCount === undefined ? "+" : "";

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
              ) : (
                <span className="font-display text-2xl font-bold tracking-tightest tabular-nums text-content-primary">
                  {formatStatistic(count, suffix)}
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

export function Categories() {
  // Real per-category counts from the database; null until (and unless) served.
  const [liveCounts, setLiveCounts] = useState<Record<string, number> | null>(null);

  useEffect(() => {
    if (!isApiConfigured) return;
    const controller = new AbortController();
    getStatistics(controller.signal)
      .then((stats) => {
        if (!stats || controller.signal.aborted) return;
        setLiveCounts(
          Object.fromEntries(stats.categories.map((c) => [c.key, c.count])),
        );
      })
      .catch(() => {
        /* keep capacity figures when live counts are unreachable */
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
              awaitingLive={isApiConfigured && liveCounts === null}
            />
          ))}
        </motion.div>
      </Section>
    </Container>
  );
}
