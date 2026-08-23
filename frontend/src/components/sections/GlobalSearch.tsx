"use client";

import { motion } from "framer-motion";
import { Container } from "@/components/ui";
import { SearchBar } from "@/components/search/SearchBar";
import { fadeInUp, transitions } from "@/lib/animations";

export function GlobalSearch() {
  return (
    <Container width="default">
      <section className="py-16 sm:py-20">
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.3 }}
          variants={fadeInUp}
          transition={transitions.slow}
          className="flex flex-col items-center gap-6 text-center"
        >
          <span className="eyebrow">Global Search</span>
          <h2 className="max-w-2xl text-balance font-display text-3xl font-bold uppercase tracking-tightest sm:text-4xl">
            Search across every biological category
          </h2>
        </motion.div>

        <div className="mx-auto mt-10 max-w-3xl">
          <SearchBar />
        </div>
      </section>
    </Container>
  );
}
