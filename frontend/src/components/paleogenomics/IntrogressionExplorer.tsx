"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Skeleton } from "@/components/ui";
import { isApiConfigured } from "@/lib/api";
import { formatStatistic } from "@/lib/statistics";
import { listIntrogression } from "@/services/paleogenomicsService";
import type { PaleogenomicIntrogression } from "@/types/paleogenomics";

export function IntrogressionExplorer() {
  const [rows, setRows] = useState<PaleogenomicIntrogression[]>([]);
  const [note, setNote] = useState<string | null>(null);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isApiConfigured) {
      setLoading(false);
      return;
    }
    const controller = new AbortController();
    listIntrogression({ limit: 50, signal: controller.signal })
      .then((payload) => {
        if (controller.signal.aborted) return;
        setRows(payload.results);
        setNote(payload.note);
        setTotal(payload.total);
        setLoading(false);
      })
      .catch(() => {
        if (!controller.signal.aborted) {
          setError(true);
          setLoading(false);
        }
      });
    return () => controller.abort();
  }, []);

  if (!isApiConfigured) {
    return (
      <div className="glass hairline p-10 text-center text-sm text-content-secondary">
        Introgression records appear once the sequence database is connected.
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex flex-col gap-3">
        <Skeleton height={120} />
        <Skeleton height={120} />
      </div>
    );
  }

  if (error) {
    return (
      <div className="glass hairline border-state-danger/40 p-10 text-center text-sm text-state-danger">
        Introgression records are temporarily unavailable.
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <p className="max-w-3xl text-sm leading-relaxed text-content-secondary">
        {note ??
          "These are Homo sapiens genomic loci with evidence of archaic ancestry. They are not DNA samples physically extracted from a Neanderthal or Denisovan specimen."}
      </p>
      <p className="font-mono text-[11px] text-content-muted">
        {formatStatistic(total)} gene-level rows · coordinates only when a cited build is stored
      </p>
      {rows.length === 0 ? (
        <div className="glass hairline p-8 text-sm text-content-secondary">
          No introgression rows are stored. Absence is not an invented map of 200 intervals.
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          {rows.map((row) => (
            <article key={row.id} className="glass hairline flex flex-col gap-2 p-5">
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <h2 className="font-display text-sm text-content-primary">
                  {row.geneName ?? row.locusName}
                </h2>
                <span className="font-mono text-[11px] uppercase text-content-muted">
                  {row.archaicSource} → {row.modernScientificName}
                </span>
              </div>
              {row.locusName && row.locusName !== row.geneName && (
                <p className="text-xs text-content-muted">{row.locusName}</p>
              )}
              <p className="text-sm text-content-secondary">{row.evidenceNotes}</p>
              {row.method && (
                <p className="text-xs text-content-muted">Method: {row.method}</p>
              )}
              {row.referenceBuild && row.chromosome && row.startPosition != null ? (
                <p className="font-mono text-[11px] text-content-muted">
                  {row.referenceBuild} {row.chromosome}:{row.startPosition}–{row.endPosition}
                </p>
              ) : (
                <p className="text-xs text-content-muted">
                  Coordinates omitted: no genome build is stored for this row.
                </p>
              )}
              {row.pubmedId && (
                <Link
                  href={`/publications/${row.pubmedId}`}
                  className="text-xs text-content-secondary hover:text-content-primary"
                >
                  PMID {row.pubmedId}
                </Link>
              )}
            </article>
          ))}
        </div>
      )}
      <p className="text-xs text-content-muted">
        Associations are not medical diagnoses and do not determine phenotype.
      </p>
    </div>
  );
}
