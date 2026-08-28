"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Button, Skeleton, StatCard } from "@/components/ui";
import { ChevronRightIcon, ExternalIcon } from "@/components/ui/Icons";
import { isApiConfigured } from "@/lib/api";
import { deriveGenomeOverviewStats } from "@/lib/genome-stats";
import { listGenomes } from "@/services/sequenceService";
import { getStatistics } from "@/services/statisticsService";
import type { GenomeAssembly } from "@/types/sequence";

function formatLength(value: number | null): string {
  if (!value) return "—";
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(2)} Mb`;
  if (value >= 1_000) return `${(value / 1_000).toFixed(1)} kb`;
  return `${value} bp`;
}

export function GenomesOverview() {
  const [genomes, setGenomes] = useState<GenomeAssembly[] | null>(null);
  const [total, setTotal] = useState<number | null>(null);
  const [organisms, setOrganisms] = useState<number | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (!isApiConfigured) return;
    const controller = new AbortController();
    Promise.all([
      listGenomes({ limit: 100, signal: controller.signal }),
      getStatistics(controller.signal),
    ])
      .then(([page, stats]) => {
        if (controller.signal.aborted) return;
        const listed = page.results ?? [];
        const derived = deriveGenomeOverviewStats(listed, page.total, stats);
        setGenomes(listed);
        setTotal(derived.stored);
        setOrganisms(derived.trackedOrganisms);
      })
      .catch(() => {
        if (!controller.signal.aborted) setError(true);
      });
    return () => controller.abort();
  }, []);

  const distinctOrganisms = genomes
    ? deriveGenomeOverviewStats(genomes, total ?? 0, null).distinctOrganisms
    : 0;
  const awaitingLive = isApiConfigured && !error && genomes === null;

  return (
    <div className="flex flex-col gap-10">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {awaitingLive ? (
          <>
            <Skeleton height={140} />
            <Skeleton height={140} />
            <Skeleton height={140} />
          </>
        ) : (
          <>
            <StatCard
              value={total ?? 0}
              label="Complete assemblies stored"
              category="genome"
              index={1}
            />
            <StatCard
              value={distinctOrganisms}
              label="Organisms with genome-level data"
              category="genome"
              index={2}
            />
            <StatCard
              value={organisms ?? 0}
              label="Organisms tracked (database)"
              category="genome"
              index={3}
            />
          </>
        )}
      </div>

      {!isApiConfigured || error ? (
        <div className="glass hairline flex flex-col gap-4 p-6">
          <span className="font-display text-sm font-bold uppercase tracking-wide text-content-primary">
            Database not connected
          </span>
          <p className="max-w-2xl text-sm leading-relaxed text-content-secondary">
            Complete genome assemblies share the same infrastructure as DNA, RNA, proteins, CRISPR
            guides and viruses, exposed through the{" "}
            <code className="font-mono text-content-primary">/genomes</code> endpoint. No assembly
            records are shown until the database is reachable — no sample or placeholder genomes are
            ever displayed.
          </p>
          <div className="flex flex-wrap gap-3 pt-2">
            <Link href="/organisms">
              <Button variant="glass" trailingIcon={<ChevronRightIcon className="h-4 w-4" />}>
                Browse organisms
              </Button>
            </Link>
            <a href="https://biowiki-api.vercel.app/docs" target="_blank" rel="noopener noreferrer">
              <Button variant="outline" trailingIcon={<ExternalIcon className="h-4 w-4" />}>
                OpenAPI /genomes
              </Button>
            </a>
          </div>
        </div>
      ) : genomes === null ? (
        <div className="glass hairline p-6 text-sm text-content-secondary">
          Loading real assemblies…
        </div>
      ) : genomes.length === 0 ? (
        <div className="glass hairline flex flex-col gap-3 p-6">
          <span className="font-display text-sm font-bold uppercase tracking-wide text-content-primary">
            No genome assemblies stored yet
          </span>
          <p className="max-w-2xl text-sm leading-relaxed text-content-secondary">
            The database is connected but no complete assemblies have been imported. Nothing is
            shown that does not exist.
          </p>
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          <span className="eyebrow">Stored assemblies · real records</span>
          <div className="hairline divide-y divide-glass-border border border-glass-border">
            {genomes.map((genome) => {
              const inner = (
                <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-3 transition-colors hover:bg-white/[0.02]">
                  <div className="flex flex-col gap-0.5">
                    <span className="font-mono text-sm text-content-primary">{genome.accession}</span>
                    <span className="text-xs italic text-content-secondary">{genome.organism}</span>
                  </div>
                  <div className="flex items-center gap-5 font-mono text-xs text-content-muted">
                    <span className="uppercase tracking-wide">{genome.assemblyLevel}</span>
                    <span>{formatLength(genome.totalLength)}</span>
                    <span>{genome.source}</span>
                    {genome.sourceUrl && (
                      <ExternalIcon className="h-4 w-4 text-content-muted" />
                    )}
                  </div>
                </div>
              );
              return (
                <Link
                  key={genome.id}
                  href={`/genomes/${encodeURIComponent(genome.accession)}`}
                  className="block"
                >
                  {inner}
                </Link>
              );
            })}
          </div>
          {total !== null && total > genomes.length && (
            <p className="text-xs text-content-muted">
              Showing {genomes.length} of {total} stored assemblies.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
