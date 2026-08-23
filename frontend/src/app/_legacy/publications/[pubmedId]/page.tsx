"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { Container } from "@/components/ui/Container";
import { GlassCard } from "@/components/ui/GlassCard";
import { getPublication } from "@/services/publicationService";
import type { PublicationDetail } from "@/types/publication";

export default function PublicationDetailPage() {
  const params = useParams<{ pubmedId: string }>();
  const pubmedId = params.pubmedId;
  const [pub, setPub] = useState<PublicationDetail | null>(null);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    getPublication(pubmedId)
      .then((record) => {
        if (!record) setNotFound(true);
        else setPub(record);
      })
      .catch(() => setNotFound(true));
  }, [pubmedId]);

  if (notFound) {
    return (
      <Container className="py-24">
        <p className="display text-2xl text-white">Publication not found</p>
      </Container>
    );
  }

  if (!pub) {
    return (
      <Container className="py-24">
        <p className="text-xs uppercase tracking-widest text-neutral-600">Loading…</p>
      </Container>
    );
  }

  return (
    <Container className="py-16">
      <span className="eyebrow">Publication</span>
      <h1 className="display mt-3 max-w-4xl text-2xl leading-snug text-white md:text-3xl">
        {pub.title}
      </h1>
      <p className="mt-4 text-sm text-neutral-400">
        {pub.authors.join(", ")}
      </p>
      <p className="mt-2 text-xs uppercase tracking-widest text-neutral-600">
        {pub.journal ?? ""} {pub.year ? `· ${pub.year}` : ""}
        {pub.volume ? ` · vol ${pub.volume}` : ""}
        {pub.pages ? ` · ${pub.pages}` : ""}
      </p>

      <div className="mt-8 flex flex-wrap gap-3">
        {pub.pubmedId && (
          <a
            href={`https://pubmed.ncbi.nlm.nih.gov/${pub.pubmedId}/`}
            target="_blank"
            rel="noreferrer"
            className="glass glass-hover px-4 py-2 text-[0.65rem] uppercase tracking-widest text-white"
          >
            PubMed {pub.pubmedId} ↗
          </a>
        )}
        {pub.doi && (
          <a
            href={`https://doi.org/${pub.doi}`}
            target="_blank"
            rel="noreferrer"
            className="glass glass-hover px-4 py-2 text-[0.65rem] uppercase tracking-widest text-white"
          >
            DOI ↗
          </a>
        )}
      </div>

      {pub.abstract && (
        <GlassCard className="mt-10 p-8" accent="#00F2FF">
          <p className="eyebrow mb-4">Abstract</p>
          <p className="text-sm leading-relaxed text-neutral-300">{pub.abstract}</p>
        </GlassCard>
      )}

      {pub.sequenceAccessions.length > 0 && (
        <div className="mt-10">
          <p className="eyebrow mb-4">Linked sequences</p>
          <div className="flex flex-wrap gap-2">
            {pub.sequenceAccessions.map((a) => (
              <Link
                key={a}
                href={`/sequences/${encodeURIComponent(a)}`}
                className="glass glass-hover px-3 py-2 font-mono text-xs text-dna"
              >
                {a}
              </Link>
            ))}
          </div>
        </div>
      )}
    </Container>
  );
}
