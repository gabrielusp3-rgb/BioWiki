"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Skeleton, StatCard, Tag } from "@/components/ui";
import { SearchIcon } from "@/components/ui/Icons";
import { fadeInUp, staggerContainer } from "@/lib/animations";
import { isApiConfigured } from "@/lib/api";
import {
  DEEXTINCTION_LABEL,
  EXTINCTION_LABEL,
  SUBSECTION_LABEL,
  labelOf,
} from "@/lib/paleogenomics";
import { formatStatistic } from "@/lib/statistics";
import { getPaleogenomicsLanding } from "@/services/paleogenomicsService";
import type {
  PaleogenomicLanding,
  PaleogenomicSpeciesCard,
} from "@/types/paleogenomics";

type DnaFilter = "any" | "yes" | "no";
type AssemblyFilter = "any" | "yes" | "no";

function SpeciesCard({ card }: { card: PaleogenomicSpeciesCard }) {
  return (
    <Link
      href={`/paleogenomics/${card.slug}`}
      className="glass hairline group flex h-full flex-col gap-4 p-5 transition-colors hover:border-white/20"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="font-display text-lg font-semibold tracking-tight text-content-primary">
            {card.commonName}
          </p>
          <p className="truncate font-body text-sm italic text-content-secondary">
            {card.scientificName}
          </p>
        </div>
        <span className="shrink-0 font-mono text-[11px] text-content-muted">
          taxid:{card.taxId}
        </span>
      </div>
      <div className="flex flex-wrap gap-2 text-[11px] uppercase tracking-wider text-content-muted">
        <span>{labelOf(SUBSECTION_LABEL, card.subsection)}</span>
        {card.extinctionStatus && (
          <span>· {labelOf(EXTINCTION_LABEL, card.extinctionStatus)}</span>
        )}
      </div>
      <p className="text-xs leading-relaxed text-content-secondary">
        {[card.geologicPeriod, card.geographicRegion, card.extinctionDateText]
          .filter(Boolean)
          .join(" · ")}
      </p>
      <div className="mt-auto grid grid-cols-2 gap-3 border-t border-glass-divider pt-3 font-mono text-[11px] text-content-muted sm:grid-cols-4">
        <span>{formatStatistic(card.sequenceCount)} seq.</span>
        <span>{formatStatistic(card.mitogenomeCount)} mt</span>
        <span>{formatStatistic(card.assemblyCount)} asm.</span>
        <span>{formatStatistic(card.publicationCount)} pubs</span>
      </div>
      {!card.paleogenomicDataAvailable && (
        <p className="text-xs text-content-muted">
          No palaeogenomic sequence records are catalogued for this taxon yet.
        </p>
      )}
    </Link>
  );
}

export function PaleogenomicsExplorer() {
  const [landing, setLanding] = useState<PaleogenomicLanding | null>(null);
  const [error, setError] = useState(false);
  const [query, setQuery] = useState("");
  const [subsection, setSubsection] = useState<string>("all");
  const [extinction, setExtinction] = useState<string>("all");
  const [dna, setDna] = useState<DnaFilter>("any");
  const [assembly, setAssembly] = useState<AssemblyFilter>("any");

  useEffect(() => {
    if (!isApiConfigured) return;
    const controller = new AbortController();
    getPaleogenomicsLanding(controller.signal)
      .then((payload) => {
        if (!controller.signal.aborted) setLanding(payload);
      })
      .catch(() => {
        if (!controller.signal.aborted) setError(true);
      });
    return () => controller.abort();
  }, []);

  const awaiting = isApiConfigured && !error && landing === null;

  const filtered = useMemo(() => {
    const cards = landing?.species ?? [];
    const q = query.trim().toLowerCase();
    return cards.filter((card) => {
      if (subsection !== "all" && card.subsection !== subsection) return false;
      if (extinction !== "all" && card.extinctionStatus !== extinction) return false;
      if (dna === "yes" && !card.paleogenomicDataAvailable) return false;
      if (dna === "no" && card.paleogenomicDataAvailable) return false;
      if (assembly === "yes" && card.assemblyCount < 1) return false;
      if (assembly === "no" && card.assemblyCount > 0) return false;
      if (!q) return true;
      return (
        card.commonName.toLowerCase().includes(q) ||
        card.scientificName.toLowerCase().includes(q) ||
        card.slug.includes(q) ||
        String(card.taxId).includes(q)
      );
    });
  }, [landing, query, subsection, extinction, dna, assembly]);

  if (!isApiConfigured) {
    return (
      <div className="glass hairline p-10 text-center text-sm text-content-secondary">
        Paleogenomics profiles appear once the sequence database is connected.
      </div>
    );
  }

  if (error) {
    return (
      <div className="glass hairline border-state-danger/40 p-10 text-center text-sm text-state-danger">
        Paleogenomics is temporarily unavailable.
      </div>
    );
  }

  const overview = landing?.overview;

  return (
    <div className="flex flex-col gap-10">
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {awaiting ? (
          Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} height={140} />)
        ) : (
          <>
            <StatCard
              value={overview?.speciesCount ?? 0}
              label="Species profiles"
              category="genome"
              index={1}
            />
            <StatCard
              value={overview?.sequenceCount ?? 0}
              label="Palaeogenomic sequences"
              category="dna"
              index={2}
            />
            <StatCard
              value={overview?.assemblyCount ?? 0}
              label="Genome assemblies"
              category="genome"
              index={3}
            />
            <StatCard
              value={overview?.publicationCount ?? 0}
              label="Linked publications"
              category="protein"
              index={4}
            />
          </>
        )}
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {awaiting ? (
          Array.from({ length: 3 }).map((_, i) => <Skeleton key={`m-${i}`} height={120} />)
        ) : (
          <>
            <StatCard
              value={overview?.archaicHomininCount ?? 0}
              label="Archaic hominin profiles"
              index={5}
            />
            <StatCard
              value={overview?.introgressionCount ?? 0}
              label="Introgression loci (living humans)"
              index={6}
            />
            <StatCard
              value={overview?.projectCount ?? 0}
              label="Projects / samples (metadata)"
              index={7}
            />
          </>
        )}
      </div>

      <p className="max-w-3xl text-sm leading-relaxed text-content-secondary">
        This is a curated collection inside BioWiki, not a separate product.
        Ancient specimen DNA remains DNA. Introgression intervals in living{" "}
        <em>Homo sapiens</em> are listed separately and are not bones.
        Counts are live database aggregates.
      </p>
      <p className="text-sm">
        <Link
          href="/paleogenomics/introgression"
          className="text-content-secondary underline-offset-4 hover:text-content-primary hover:underline"
        >
          Archaic introgression in living humans
        </Link>
        {" · "}
        <Link
          href="/paleogenomics/raphus-cucullatus"
          className="text-content-secondary underline-offset-4 hover:text-content-primary hover:underline"
        >
          Dodo
        </Link>
        {" · "}
        <Link
          href="/paleogenomics/thylacinus-cynocephalus"
          className="text-content-secondary underline-offset-4 hover:text-content-primary hover:underline"
        >
          Thylacine
        </Link>
        {" · "}
        <Link
          href="/paleogenomics/coelodonta-antiquitatis"
          className="text-content-secondary underline-offset-4 hover:text-content-primary hover:underline"
        >
          Woolly rhinoceros
        </Link>
      </p>

      {landing?.featured && landing.featured.length > 0 && (
        <section>
          <span className="eyebrow mb-3 block">Featured</span>
          <motion.div
            variants={staggerContainer(0.06, 0)}
            initial="hidden"
            animate="visible"
            className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3"
          >
            {landing.featured.map((card) => (
              <motion.div key={card.slug} variants={fadeInUp}>
                <SpeciesCard card={card} />
              </motion.div>
            ))}
          </motion.div>
        </section>
      )}

      <div className="flex flex-col gap-4">
        <div className="glass hairline flex items-center gap-3 px-4">
          <SearchIcon className="h-5 w-5 shrink-0 text-content-secondary" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search common name, scientific name or TaxID…"
            aria-label="Filter Paleogenomics species"
            className="h-14 w-full bg-transparent font-body text-base text-content-primary outline-none placeholder:text-content-muted"
          />
        </div>
        <div className="flex flex-wrap gap-2">
          <Tag active={subsection === "all"} onClick={() => setSubsection("all")}>
            All groups
          </Tag>
          {Object.entries(SUBSECTION_LABEL).map(([key, label]) => (
            <Tag key={key} active={subsection === key} onClick={() => setSubsection(key)}>
              {label}
            </Tag>
          ))}
        </div>
        <div className="flex flex-wrap gap-2">
          <Tag active={extinction === "all"} onClick={() => setExtinction("all")}>
            Any extinction status
          </Tag>
          {Object.entries(EXTINCTION_LABEL).map(([key, label]) => (
            <Tag key={key} active={extinction === key} onClick={() => setExtinction(key)}>
              {label}
            </Tag>
          ))}
        </div>
        <div className="flex flex-wrap gap-2">
          <Tag active={dna === "any"} onClick={() => setDna("any")}>
            DNA: any
          </Tag>
          <Tag active={dna === "yes"} onClick={() => setDna("yes")}>
            Ancient DNA catalogued
          </Tag>
          <Tag active={dna === "no"} onClick={() => setDna("no")}>
            No sequence records yet
          </Tag>
          <Tag active={assembly === "any"} onClick={() => setAssembly("any")}>
            Assemblies: any
          </Tag>
          <Tag active={assembly === "yes"} onClick={() => setAssembly("yes")}>
            Assembly available
          </Tag>
          <Tag active={assembly === "no"} onClick={() => setAssembly("no")}>
            No assembly
          </Tag>
        </div>
      </div>

      {landing?.notes && landing.notes.length > 0 && (
        <ul className="glass hairline flex flex-col gap-2 p-5 text-sm text-content-secondary">
          {landing.notes.map((note) => (
            <li key={note}>{note}</li>
          ))}
        </ul>
      )}

      <section>
        <div className="mb-3 flex items-center justify-between">
          <span className="eyebrow">Species</span>
          <span className="font-mono text-[11px] text-content-muted">
            {awaiting ? "…" : `${filtered.length} shown`}
          </span>
        </div>
        {awaiting ? (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} height={180} />
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <div className="glass hairline p-10 text-center text-sm text-content-secondary">
            No profiles match these filters. Unknown is shown rather than invented.
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {filtered.map((card) => (
              <SpeciesCard key={card.slug} card={card} />
            ))}
          </div>
        )}
      </section>

      <p className="text-xs text-content-muted">
        De-extinction labels describe research status, not resurrection.
        {overview?.lastReviewedOn
          ? ` Last scientific review of curated narratives: ${overview.lastReviewedOn}.`
          : ""}{" "}
        {labelOf(DEEXTINCTION_LABEL, "proxy_trait_engineering")} is not the historical organism.
      </p>
    </div>
  );
}
