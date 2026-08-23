"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { Container } from "@/components/ui/Container";
import { GlassCard } from "@/components/ui/GlassCard";
import { formatNumber } from "@/lib/format";
import { getOrganism } from "@/services/organismService";
import type { Organism } from "@/types/organism";

export default function OrganismDetailPage() {
  const params = useParams<{ identifier: string }>();
  const identifier = decodeURIComponent(params.identifier);
  const [org, setOrg] = useState<Organism | null>(null);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    getOrganism(identifier)
      .then(setOrg)
      .catch(() => setNotFound(true));
  }, [identifier]);

  if (notFound) {
    return (
      <Container className="py-24">
        <p className="display text-2xl text-white">Organism not found</p>
        <Link href="/organisms" className="mt-4 inline-block text-sm text-dna">
          ← All organisms
        </Link>
      </Container>
    );
  }

  if (!org) {
    return (
      <Container className="py-24">
        <p className="text-xs uppercase tracking-widest text-neutral-600">Loading…</p>
      </Container>
    );
  }

  return (
    <Container className="py-16">
      <Link href="/organisms" className="eyebrow">
        ← Organisms
      </Link>
      <span className="mt-4 block text-[0.65rem] font-semibold uppercase tracking-widest text-neutral-500">
        {org.group} · {org.rank ?? "—"} · tax {org.taxId}
      </span>
      <h1 className="display mt-2 text-4xl italic text-white">{org.scientificName}</h1>
      {org.commonName && <p className="mt-1 text-neutral-400">{org.commonName}</p>}

      <div className="mt-10 grid gap-8 lg:grid-cols-3">
        <GlassCard className="p-8">
          <p className="display text-5xl text-dna">
            {formatNumber(org.sequenceCount ?? 0)}
          </p>
          <p className="mt-2 text-xs uppercase tracking-widest text-neutral-500">
            stored sequences
          </p>
          <Link
            href={`/search?q=${encodeURIComponent(org.scientificName)}`}
            className="mt-6 inline-block bg-dna px-4 py-3 text-[0.65rem] font-semibold uppercase tracking-widest text-black"
          >
            Browse sequences
          </Link>
        </GlassCard>

        <GlassCard className="p-8 lg:col-span-2">
          <p className="eyebrow mb-4">Taxonomic lineage</p>
          {org.lineage && org.lineage.length ? (
            <div className="flex flex-wrap items-center gap-2 text-sm text-neutral-300">
              {org.lineage.map((l, i) => (
                <span key={i} className="flex items-center gap-2">
                  {i > 0 && <span className="text-neutral-700">›</span>}
                  <span className="glass px-3 py-1">{l}</span>
                </span>
              ))}
            </div>
          ) : (
            <p className="text-sm text-neutral-500">No lineage stored.</p>
          )}
          <div className="mt-8 flex gap-4">
            <a
              href={`https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id=${org.taxId}`}
              target="_blank"
              rel="noreferrer"
              className="text-xs text-dna"
            >
              NCBI Taxonomy ↗
            </a>
          </div>
        </GlassCard>
      </div>
    </Container>
  );
}
