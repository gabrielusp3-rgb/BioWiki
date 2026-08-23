"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { SiteHeader } from "@/components/layout/SiteHeader";
import { SiteFooter } from "@/components/layout/SiteFooter";
import { Container, Section } from "@/components/ui";
import { Badge } from "@/components/ui/Badge";
import { formatBases, formatDate, formatNumber } from "@/lib/format";
import { getGenome } from "@/services/sequenceService";
import type { GenomeAssembly } from "@/types/sequence";

export default function GenomeDetailPage() {
  const params = useParams<{ accession: string }>();
  const accession = decodeURIComponent(params.accession);
  const [g, setG] = useState<GenomeAssembly | null>(null);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    getGenome(accession)
      .then((record) => {
        if (!record) setNotFound(true);
        else setG(record);
      })
      .catch(() => setNotFound(true));
  }, [accession]);

  if (notFound) {
    return (
      <>
        <SiteHeader activeHref="/genomes" />
        <main id="main" className="pt-16">
          <Container className="py-24">
            <p className="font-display text-2xl text-content-primary">Genome not found</p>
            <Link href="/genomes" className="mt-4 inline-block text-sm text-category-dna">
              ← All genomes
            </Link>
          </Container>
        </main>
        <SiteFooter />
      </>
    );
  }

  if (!g) {
    return (
      <>
        <SiteHeader activeHref="/genomes" />
        <main id="main" className="pt-16">
          <Container className="py-24">
            <p className="text-xs uppercase tracking-widest text-content-muted">Loading…</p>
          </Container>
        </main>
        <SiteFooter />
      </>
    );
  }

  const meta: [string, string][] = [
    ["Accession", g.accession],
    ["Assembly", g.assemblyName ?? "—"],
    ["Organism", g.organism],
    ["Tax ID", String(g.taxId)],
    ["Source", g.source],
    ["Level", g.assemblyLevel],
    ["Total length", g.totalLength ? formatBases(g.totalLength) : "—"],
    ["Chromosomes", g.chromosomeCount != null ? formatNumber(g.chromosomeCount) : "—"],
    ["GC content", g.gcContent != null ? `${(g.gcContent * 100).toFixed(1)}%` : "—"],
    ["Released", formatDate(g.releaseDate)],
  ];

  return (
    <>
      <SiteHeader activeHref="/genomes" />
      <main id="main" className="pt-16">
        <Container width="wide">
          <Section
            eyebrow="Genome assembly"
            title={g.assemblyName ?? g.organism}
            description="Assembly-level metadata as stored in the database — never fabricated."
          >
            <Link href="/genomes" className="eyebrow">
              ← Genomes
            </Link>
            <div className="mt-4 flex items-center gap-3">
              <Badge category="genome" />
              <span className="font-mono text-sm text-category-genome">{g.accession}</span>
            </div>
            {g.description && (
              <p className="mt-4 max-w-3xl text-sm text-content-secondary">{g.description}</p>
            )}

            <div className="glass hairline relative mt-10 overflow-hidden p-8">
              <span
                className="absolute left-0 top-0 h-full w-[3px]"
                style={{ background: "#7C5CFF" }}
              />
              <dl className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {meta.map(([k, v]) => (
                  <div key={k} className="border-b border-glass-divider pb-2">
                    <dt className="text-[0.65rem] uppercase tracking-widest text-content-muted">
                      {k}
                    </dt>
                    <dd className="mt-1 text-sm text-content-primary">{v}</dd>
                  </div>
                ))}
              </dl>
              {g.sourceUrl && (
                <a
                  href={g.sourceUrl}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-8 inline-block bg-category-genome px-4 py-3 text-[0.65rem] font-semibold uppercase tracking-widest text-black"
                >
                  View at source ↗
                </a>
              )}
            </div>
          </Section>
        </Container>
      </main>
      <SiteFooter />
    </>
  );
}
