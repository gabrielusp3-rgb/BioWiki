"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Container, OrganismCard, Section, Skeleton, Button } from "@/components/ui";
import { ChevronRightIcon } from "@/components/ui/Icons";
import { fadeInUp, staggerContainer } from "@/lib/animations";
import { getFeaturedOrganisms } from "@/services/organismService";
import { isApiConfigured } from "@/lib/api";
import { REFERENCE_ORGANISMS } from "@/lib/organisms";
import type { Organism } from "@/types/organism";

export interface FeaturedOrganismsProps {
  limit?: number;
  /** Pre-supplied data (e.g. from a server component); skips client fetching. */
  organisms?: Organism[];
}

export function FeaturedOrganisms({ limit = 8, organisms }: FeaturedOrganismsProps) {
  const [items, setItems] = useState<Organism[]>(
    organisms ?? (isApiConfigured ? [] : REFERENCE_ORGANISMS.slice(0, limit)),
  );
  const [loading, setLoading] = useState(organisms ? false : isApiConfigured);

  useEffect(() => {
    if (organisms || !isApiConfigured) return;
    const controller = new AbortController();
    setLoading(true);
    getFeaturedOrganisms(limit, controller.signal)
      .then((data) => setItems(data))
      .catch(() => setItems(REFERENCE_ORGANISMS.slice(0, limit)))
      .finally(() => setLoading(false));
    return () => controller.abort();
  }, [limit, organisms]);

  return (
    <Container width="wide">
      <Section
        eyebrow="Featured Organisms"
        title="Life across the tree of biology"
        description="Model organisms and reference species with canonical NCBI taxonomy. Sequence totals are served directly from the database."
      >
        <div className="mb-8 flex justify-end">
          <Link href="/organisms">
            <Button variant="glass" size="sm" trailingIcon={<ChevronRightIcon className="h-4 w-4" />}>
              View all organisms
            </Button>
          </Link>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {Array.from({ length: limit }).map((_, i) => (
              <Skeleton key={i} height={340} />
            ))}
          </div>
        ) : (
          <motion.div
            variants={staggerContainer(0.06, 0.04)}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.1 }}
            className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4"
          >
            {items.map((organism) => (
              <motion.div key={organism.id} variants={fadeInUp} className="h-full">
                <OrganismCard organism={organism} />
              </motion.div>
            ))}
          </motion.div>
        )}
      </Section>
    </Container>
  );
}
