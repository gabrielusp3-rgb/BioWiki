"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Badge, Skeleton } from "@/components/ui";
import { ExternalIcon } from "@/components/ui/Icons";
import { isApiConfigured } from "@/lib/api";
import type { CategoryKey } from "@/lib/design-tokens";
import { GROUP_COLOR, GROUP_LABEL, ncbiTaxonomyUrl } from "@/lib/organisms";
import { formatStatistic } from "@/lib/statistics";
import { getOrganism } from "@/services/organismService";
import { listByOrganism, listGenomes } from "@/services/sequenceService";
import { listPublications } from "@/services/publicationService";
import type { Organism } from "@/types/organism";
import type { Publication } from "@/types/publication";
import type { GenomeAssembly, SequenceSummary } from "@/types/sequence";

type Status = "loading" | "ready" | "notfound" | "unavailable" | "error";

const CATEGORIES: { key: "dna" | "rna" | "protein" | "crispr" | "virus"; label: string; category: CategoryKey }[] = [
  { key: "dna", label: "DNA sequences", category: "dna" },
  { key: "rna", label: "RNA sequences", category: "rna" },
  { key: "protein", label: "Proteins", category: "protein" },
  { key: "crispr", label: "CRISPR records", category: "crispr" },
  { key: "virus", label: "Viral sequences", category: "virus" },
];

interface CategoryData {
  results: SequenceSummary[];
  total: number;
}

function SequenceRow({ item, category }: { item: SequenceSummary; category: CategoryKey }) {
  const length = item.length ?? item.guideLength;
  return (
    <Link
      href={`/sequences/${encodeURIComponent(item.accession)}`}
      className="glass hairline group flex w-full items-center gap-4 px-5 py-3.5 transition-colors hover:border-white/20"
    >
      <Badge category={category} />
      <span className="flex min-w-0 flex-1 flex-col">
        <span className="truncate font-body text-sm text-content-primary">{item.name}</span>
        <span className="truncate text-xs text-content-secondary">{item.source}</span>
      </span>
      <span className="hidden shrink-0 font-mono text-xs text-content-secondary sm:block">
        {item.accession}
      </span>
      {length !== undefined && (
        <span className="shrink-0 font-mono text-[11px] text-content-muted">
          {formatStatistic(length)} {category === "protein" ? "aa" : "bp"}
        </span>
      )}
    </Link>
  );
}

function initials(name: string): string {
  return name
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? "")
    .join("");
}

export function OrganismDetailContent({ identifier }: { identifier: string }) {
  const [status, setStatus] = useState<Status>("loading");
  const [organism, setOrganism] = useState<Organism | null>(null);
  const [sections, setSections] = useState<Partial<Record<string, CategoryData>>>({});
  const [genomes, setGenomes] = useState<GenomeAssembly[]>([]);
  const [publications, setPublications] = useState<Publication[]>([]);

  useEffect(() => {
    const controller = new AbortController();
    setStatus("loading");
    getOrganism(identifier, controller.signal)
      .then(async (record) => {
        if (controller.signal.aborted) return;
        if (record === null) {
          setStatus(isApiConfigured ? "notfound" : "unavailable");
          return;
        }
        setOrganism(record);
        setStatus("ready");
        if (!isApiConfigured) return;

        const name = record.scientificName;
        const [categoryData, genomeData, publicationData] = await Promise.all([
          Promise.all(
            CATEGORIES.map(async ({ key }) => {
              try {
                const response = await listByOrganism(key, name, {
                  limit: 6,
                  signal: controller.signal,
                });
                return [key, { results: response.results, total: response.total }] as const;
              } catch {
                return [key, { results: [], total: 0 }] as const;
              }
            }),
          ),
          listGenomes({ organism: name, limit: 12, signal: controller.signal }).catch(
            () => ({ results: [] as GenomeAssembly[], total: 0, nextCursor: null }),
          ),
          listPublications({ organism: name, limit: 8, signal: controller.signal }).catch(
            () => ({ results: [] as Publication[], total: 0, nextCursor: null }),
          ),
        ]);
        if (controller.signal.aborted) return;
        setSections(Object.fromEntries(categoryData));
        setGenomes(genomeData.results);
        setPublications(publicationData.results);
      })
      .catch(() => {
        if (!controller.signal.aborted) setStatus("error");
      });
    return () => controller.abort();
  }, [identifier]);

  if (status === "loading") {
    return (
      <div className="flex flex-col gap-4">
        <Skeleton height={200} />
        <Skeleton height={320} />
      </div>
    );
  }

  if (status === "notfound" || status === "unavailable") {
    return (
      <div className="glass hairline flex flex-col items-center gap-4 p-10 text-center">
        <p className="text-sm text-content-secondary">
          {status === "notfound" ? (
            <>
              No organism matching{" "}
              <span className="font-mono text-content-primary">{identifier}</span>{" "}
              exists in the database.
            </>
          ) : (
            "Organism records are served from the database. Connect the backend to view this page."
          )}
        </p>
        <Link
          href="/organisms"
          className="border border-glass-border px-4 py-2 font-display text-xs font-semibold uppercase tracking-wide text-content-secondary transition-colors hover:border-white/30 hover:text-content-primary"
        >
          Browse organisms
        </Link>
      </div>
    );
  }

  if (status === "error" || !organism) {
    return (
      <div className="glass hairline border-state-danger/40 p-10 text-center text-sm text-state-danger">
        The organism could not be loaded. Please try again.
      </div>
    );
  }

  const color = GROUP_COLOR[organism.group] ?? "#00F2FF";
  const totalListed = CATEGORIES.reduce(
    (sum, { key }) => sum + (sections[key]?.total ?? 0),
    0,
  );

  return (
    <div className="flex flex-col gap-10">
      {/* Identity */}
      <div className="glass hairline flex flex-col gap-6 p-6 sm:flex-row sm:items-start">
        <div
          className="grid h-24 w-24 shrink-0 place-items-center border border-glass-divider"
          style={{
            background: `radial-gradient(120% 120% at 30% 0%, ${color}1F, transparent 60%), #0A0A0A`,
          }}
        >
          <span
            className="font-display text-3xl font-bold tracking-tightest"
            style={{ color, textShadow: `0 0 30px ${color}59` }}
          >
            {initials(organism.scientificName)}
          </span>
        </div>

        <div className="flex min-w-0 flex-1 flex-col gap-3">
          <div className="flex flex-wrap items-center gap-3">
            <Badge
              tone="neutral"
              dot
              style={{ color, borderColor: `${color}59`, backgroundColor: `${color}14` }}
            >
              {GROUP_LABEL[organism.group]}
            </Badge>
            {organism.rank && (
              <span className="font-mono text-xs uppercase tracking-wider text-content-muted">
                {organism.rank}
              </span>
            )}
            <a
              href={ncbiTaxonomyUrl(organism.taxId)}
              target="_blank"
              rel="noopener noreferrer"
              className="ml-auto flex items-center gap-2 border border-glass-border px-3 py-1.5 font-mono text-xs text-content-secondary transition-colors hover:border-white/30 hover:text-content-primary"
            >
              taxid:{organism.taxId}
              <ExternalIcon className="h-3.5 w-3.5" />
            </a>
          </div>
          <h1 className="font-display text-3xl font-bold tracking-tightest text-content-primary">
            {organism.commonName ?? organism.scientificName}
          </h1>
          <p className="font-body text-base italic text-content-secondary">
            {organism.scientificName}
          </p>
          {(organism.lineage ?? []).length > 0 && (
            <div className="flex flex-wrap items-center gap-1.5 border-t border-glass-divider pt-3 text-xs text-content-secondary">
              {(organism.lineage ?? []).map((node, i) => (
                <span key={`${node}-${i}`} className="flex items-center gap-1.5">
                  {i > 0 && <span className="text-content-muted">/</span>}
                  <span>{node}</span>
                </span>
              ))}
            </div>
          )}
          <div className="flex items-center gap-6 border-t border-glass-divider pt-3">
            <div className="flex flex-col">
              <span className="font-display text-xl font-bold tabular-nums text-content-primary">
                {organism.sequenceCount !== null
                  ? formatStatistic(organism.sequenceCount)
                  : totalListed > 0
                    ? formatStatistic(totalListed)
                    : "—"}
              </span>
              <span className="text-[10px] uppercase tracking-wider text-content-muted">
                Sequences in database
              </span>
            </div>
            <Link
              href={`/search?q=${encodeURIComponent(organism.scientificName)}`}
              className="ml-auto border px-4 py-2 font-display text-[11px] font-semibold uppercase tracking-wide transition-colors"
              style={{ color, borderColor: `${color}59` }}
            >
              Search all records
            </Link>
          </div>
        </div>
      </div>

      {/* Per-category records */}
      {CATEGORIES.map(({ key, label, category }) => {
        const data = sections[key];
        if (!data || data.results.length === 0) return null;
        return (
          <section key={key}>
            <div className="mb-3 flex items-center justify-between">
              <span className="eyebrow">{label}</span>
              <span className="font-mono text-[11px] text-content-muted">
                {formatStatistic(data.total)} record{data.total === 1 ? "" : "s"}
              </span>
            </div>
            <div className="flex flex-col gap-3">
              {data.results.map((item) => (
                <SequenceRow key={item.id} item={item} category={category} />
              ))}
            </div>
          </section>
        );
      })}

      {isApiConfigured && totalListed === 0 && (
        <div className="glass hairline p-8 text-center text-sm text-content-secondary">
          No sequence records for {organism.scientificName} have been ingested yet.
          Only real, imported data is ever listed here.
        </div>
      )}

      {/* Genome assemblies */}
      {genomes.length > 0 && (
        <section>
          <div className="mb-3 flex items-center justify-between">
            <span className="eyebrow">Genome assemblies</span>
            <span className="font-mono text-[11px] text-content-muted">
              {genomes.length} assembl{genomes.length === 1 ? "y" : "ies"}
            </span>
          </div>
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            {genomes.map((genome) => (
              <div key={genome.id} className="glass hairline flex flex-col gap-2 p-5">
                <div className="flex items-center justify-between gap-3">
                  <span className="font-mono text-sm text-content-primary">
                    {genome.accession}
                  </span>
                  <Badge category="genome">{genome.assemblyLevel}</Badge>
                </div>
                {genome.assemblyName && (
                  <span className="font-body text-sm text-content-secondary">
                    {genome.assemblyName}
                  </span>
                )}
                <div className="flex flex-wrap gap-x-5 gap-y-1 border-t border-glass-divider pt-2 font-mono text-[11px] text-content-muted">
                  {genome.totalLength !== null && (
                    <span>{formatStatistic(genome.totalLength)} bp</span>
                  )}
                  {genome.chromosomeCount !== null && (
                    <span>{genome.chromosomeCount} chromosomes</span>
                  )}
                  {genome.releaseDate && <span>{genome.releaseDate}</span>}
                </div>
                {genome.sourceUrl && (
                  <a
                    href={genome.sourceUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="mt-1 flex w-fit items-center gap-2 text-xs text-content-secondary hover:text-content-primary"
                  >
                    View at source
                    <ExternalIcon className="h-3 w-3" />
                  </a>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Publications */}
      {publications.length > 0 && (
        <section>
          <span className="eyebrow mb-3 block">Publications</span>
          <div className="flex flex-col gap-3">
            {publications.map((publication) => {
              const authors =
                publication.authors.length > 3
                  ? `${publication.authors.slice(0, 3).join(", ")} et al.`
                  : publication.authors.join(", ");
              const line = [authors, publication.journal, publication.year]
                .filter(Boolean)
                .join(" · ");
              const inner = (
                <span className="flex min-w-0 flex-1 flex-col gap-1">
                  <span className="font-body text-sm text-content-primary">
                    {publication.title}
                  </span>
                  {line && (
                    <span className="truncate text-xs text-content-secondary">{line}</span>
                  )}
                </span>
              );
              const className =
                "glass hairline flex w-full items-start gap-4 px-5 py-4 transition-colors hover:border-white/20";
              return publication.pubmedId ? (
                <Link
                  key={publication.id}
                  href={`/publications/${publication.pubmedId}`}
                  className={className}
                >
                  {inner}
                  <span className="shrink-0 font-mono text-[11px] text-content-muted">
                    PMID {publication.pubmedId}
                  </span>
                </Link>
              ) : (
                <div key={publication.id} className={className}>
                  {inner}
                </div>
              );
            })}
          </div>
        </section>
      )}
    </div>
  );
}
