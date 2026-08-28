"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Badge, Button, Container } from "@/components/ui";
import { DownloadIcon, ChevronRightIcon } from "@/components/ui/Icons";
import { fadeInUp, staggerContainer, transitions } from "@/lib/animations";
import { categories } from "@/lib/design-tokens";
import { CATEGORY_META } from "@/lib/categories";

export function Hero() {
  return (
    <section className="relative flex min-h-[100dvh] items-center overflow-hidden pt-16">
      {/* Scientific grid + corner framing float above the BackgroundDNA */}
      <div
        aria-hidden
        className="grid-lines pointer-events-none absolute inset-0 opacity-[0.35] [mask-image:radial-gradient(ellipse_at_center,black,transparent_75%)]"
      />

      <Container width="wide" className="relative z-10">
        <motion.div
          variants={staggerContainer(0.1, 0.1)}
          initial="hidden"
          animate="visible"
          className="flex max-w-4xl flex-col gap-8"
        >
          {/* Eyebrow */}
          <motion.div variants={fadeInUp} className="flex items-center gap-3">
            <span className="h-1.5 w-1.5 bg-category-dna shadow-glow-dna" />
            <span className="eyebrow">Universal Biological Sequence Database</span>
          </motion.div>

          {/* Wordmark */}
          <motion.h1
            variants={fadeInUp}
            className="font-display text-6xl font-bold uppercase leading-[0.92] tracking-tightest text-content-primary sm:text-7xl lg:text-8xl xl:text-9xl"
          >
            <span className="relative inline-block">
              Bio
              <span
                className="text-transparent"
                style={{
                  WebkitTextStroke: "1px rgba(0,242,255,0.55)",
                }}
              >
                Wiki
              </span>
            </span>
          </motion.h1>

          {/* Subtitle */}
          <motion.p
            variants={fadeInUp}
            className="max-w-2xl text-balance font-display text-lg font-medium uppercase tracking-wide text-content-secondary sm:text-xl"
          >
            Explore the biological diversity of life through real
            molecular sequences.
          </motion.p>

          {/* Supporting description */}
          <motion.p
            variants={fadeInUp}
            className="max-w-xl text-balance text-base leading-relaxed text-content-secondary"
          >
            DNA, RNA, proteins, CRISPR guides, genomes and viral sequences from
            public archives, stored locally and served as they were imported.
          </motion.p>

          {/* Actions */}
          <motion.div variants={fadeInUp} className="flex flex-col gap-4 pt-2">
            <div className="glass hairline flex w-fit max-w-full flex-wrap items-center gap-3 p-3">
              <Link href="/search">
                <Button
                  variant="primary"
                  size="lg"
                  trailingIcon={<ChevronRightIcon className="h-4 w-4" />}
                >
                  Explore Database
                </Button>
              </Link>
              <Link href="/downloads">
                <Button
                  variant="outline"
                  size="lg"
                  leadingIcon={<DownloadIcon className="h-4 w-4" />}
                >
                  Download Datasets
                </Button>
              </Link>
            </div>
          </motion.div>

          {/* Category strip */}
          <motion.div variants={fadeInUp} className="flex flex-wrap items-center gap-2 pt-4">
            {categories.map((key) => (
              <Badge key={key} category={key} dot>
                {CATEGORY_META[key].label}
              </Badge>
            ))}
          </motion.div>
        </motion.div>
      </Container>

      {/* Scroll cue */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ ...transitions.slow, delay: 0.9 }}
        className="pointer-events-none absolute inset-x-0 bottom-8 z-10 flex justify-center"
      >
        <div className="flex flex-col items-center gap-2 text-content-muted">
          <span className="text-[10px] uppercase tracking-wider">Scroll</span>
          <span className="h-10 w-px bg-gradient-to-b from-category-dna/60 to-transparent" />
        </div>
      </motion.div>
    </section>
  );
}
