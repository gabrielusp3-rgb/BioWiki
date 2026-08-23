"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Skeleton } from "@/components/ui";
import { ExternalIcon } from "@/components/ui/Icons";
import { isApiConfigured } from "@/lib/api";
import { getPublication } from "@/services/publicationService";
import type { PublicationDetail } from "@/types/publication";

type Status = "loading" | "ready" | "notfound" | "unavailable" | "error";

function ExternalChip({ label, href }: { label: string; href: string }) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="flex items-center gap-2 border border-glass-border px-3 py-1.5 font-display text-[11px] font-semibold uppercase tracking-wide text-content-secondary transition-colors hover:border-white/30 hover:text-content-primary"
    >
      {label}
      <ExternalIcon className="h-3.5 w-3.5" />
    </a>
  );
}

export function PublicationDetailContent({ pubmedId }: { pubmedId: string }) {
  const [status, setStatus] = useState<Status>(isApiConfigured ? "loading" : "unavailable");
  const [publication, setPublication] = useState<PublicationDetail | null>(null);

  useEffect(() => {
    if (!isApiConfigured) return;
    const controller = new AbortController();
    setStatus("loading");
    getPublication(pubmedId, controller.signal)
      .then((record) => {
        if (controller.signal.aborted) return;
        if (record === null) {
          setStatus("notfound");
          return;
        }
        setPublication(record);
        setStatus("ready");
      })
      .catch(() => {
        if (!controller.signal.aborted) setStatus("error");
      });
    return () => controller.abort();
  }, [pubmedId]);

  if (status === "loading") {
    return (
      <div className="flex flex-col gap-4">
        <Skeleton height={160} />
        <Skeleton height={240} />
      </div>
    );
  }

  if (status === "unavailable") {
    return (
      <div className="glass hairline p-10 text-center text-sm text-content-secondary">
        Publication records are served from the database. Connect the backend to
        view this article.
      </div>
    );
  }

  if (status === "notfound") {
    return (
      <div className="glass hairline flex flex-col items-center gap-4 p-10 text-center">
        <p className="text-sm text-content-secondary">
          No publication with PMID{" "}
          <span className="font-mono text-content-primary">{pubmedId}</span> exists
          in the database.
        </p>
        <Link
          href="/search"
          className="border border-glass-border px-4 py-2 font-display text-xs font-semibold uppercase tracking-wide text-content-secondary transition-colors hover:border-white/30 hover:text-content-primary"
        >
          Search the database
        </Link>
      </div>
    );
  }

  if (status === "error" || !publication) {
    return (
      <div className="glass hairline border-state-danger/40 p-10 text-center text-sm text-state-danger">
        The publication could not be loaded. Please try again.
      </div>
    );
  }

  const citation = [
    publication.journal,
    publication.volume ? `vol. ${publication.volume}` : null,
    publication.pages ? `pp. ${publication.pages}` : null,
    publication.year,
  ]
    .filter(Boolean)
    .join(" · ");

  return (
    <div className="flex flex-col gap-8">
      {/* Bibliographic record */}
      <div className="glass hairline flex flex-col gap-4 p-6">
        <h1 className="font-display text-2xl font-bold tracking-tightest text-content-primary">
          {publication.title}
        </h1>
        {publication.authors.length > 0 && (
          <p className="font-body text-sm text-content-secondary">
            {publication.authors.join(", ")}
          </p>
        )}
        {citation && (
          <p className="font-body text-sm italic text-content-secondary">{citation}</p>
        )}
        <div className="flex flex-wrap items-center gap-2 border-t border-glass-divider pt-4">
          {publication.pubmedId && (
            <span className="font-mono text-xs text-content-muted">
              PMID {publication.pubmedId}
            </span>
          )}
          {publication.doi && (
            <span className="font-mono text-xs text-content-muted">
              DOI {publication.doi}
            </span>
          )}
          <span className="ml-auto flex flex-wrap gap-2">
            {publication.pubmedId && (
              <ExternalChip
                label="PubMed"
                href={`https://pubmed.ncbi.nlm.nih.gov/${publication.pubmedId}/`}
              />
            )}
            {publication.doi && (
              <ExternalChip label="DOI" href={`https://doi.org/${publication.doi}`} />
            )}
            {publication.pmcId && (
              <ExternalChip
                label="PMC"
                href={`https://www.ncbi.nlm.nih.gov/pmc/articles/${publication.pmcId}/`}
              />
            )}
          </span>
        </div>
      </div>

      {/* Abstract */}
      {publication.abstract && (
        <section>
          <span className="eyebrow mb-3 block">Abstract</span>
          <div className="glass hairline p-6">
            <p className="whitespace-pre-wrap font-body text-sm leading-relaxed text-content-secondary">
              {publication.abstract}
            </p>
          </div>
        </section>
      )}

      {/* Linked sequence records */}
      {publication.sequenceAccessions.length > 0 && (
        <section>
          <span className="eyebrow mb-3 block">
            Linked sequence records · {publication.sequenceAccessions.length}
          </span>
          <div className="flex flex-wrap gap-2">
            {publication.sequenceAccessions.map((accession) => (
              <Link
                key={accession}
                href={`/sequences/${encodeURIComponent(accession)}`}
                className="border border-glass-border px-3 py-1.5 font-mono text-xs text-content-secondary transition-colors hover:border-white/30 hover:text-content-primary"
              >
                {accession}
              </Link>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
