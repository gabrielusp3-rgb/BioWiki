"use client";

import Link from "next/link";
import { Button, Skeleton } from "@/components/ui";
import { SearchIcon } from "@/components/ui/Icons";
import { cn } from "@/lib/cn";
import { formatStatistic } from "@/lib/statistics";
import { usePublications } from "@/hooks/usePublications";
import type { Publication } from "@/types/publication";

function authorsLine(publication: Publication): string {
  if (publication.authors.length === 0) return "";
  if (publication.authors.length > 3) {
    return `${publication.authors.slice(0, 3).join(", ")} et al.`;
  }
  return publication.authors.join(", ");
}

function PublicationRow({ publication }: { publication: Publication }) {
  const meta = [authorsLine(publication), publication.journal, publication.year]
    .filter(Boolean)
    .join(" · ");
  const inner = (
    <>
      <span className="font-body text-sm text-content-primary">{publication.title}</span>
      {meta && <span className="truncate text-xs text-content-secondary">{meta}</span>}
    </>
  );

  if (publication.pubmedId) {
    return (
      <Link
        href={`/publications/${publication.pubmedId}`}
        className="glass hairline group flex w-full items-start gap-4 px-5 py-4 transition-colors hover:border-white/20"
      >
        <span className="flex min-w-0 flex-1 flex-col gap-1">{inner}</span>
        <span className="shrink-0 font-mono text-[11px] text-content-muted">
          PMID {publication.pubmedId}
        </span>
      </Link>
    );
  }

  if (publication.url) {
    return (
      <a
        href={publication.url}
        target="_blank"
        rel="noopener noreferrer"
        className="glass hairline group flex w-full items-start gap-4 px-5 py-4 transition-colors hover:border-white/20"
      >
        <span className="flex min-w-0 flex-1 flex-col gap-1">{inner}</span>
      </a>
    );
  }

  return (
    <div className="glass hairline flex w-full items-start gap-4 px-5 py-4">
      <span className="flex min-w-0 flex-1 flex-col gap-1">{inner}</span>
    </div>
  );
}

export function PublicationsExplorer() {
  const pubs = usePublications();
  const from = pubs.pageIndex * pubs.pageSize + 1;
  const to = pubs.pageIndex * pubs.pageSize + pubs.results.length;

  return (
    <div className="flex flex-col gap-6">
      <div
        className={cn(
          "glass hairline flex items-center gap-3 px-4 transition-colors duration-200",
          "focus-within:border-category-dna/50",
        )}
      >
        <SearchIcon className="h-5 w-5 shrink-0 text-content-secondary" />
        <input
          value={pubs.query}
          onChange={(e) => pubs.setQuery(e.target.value)}
          placeholder="Search publications by title, abstract or PMID…"
          aria-label="Search publications"
          className="h-14 w-full bg-transparent font-body text-base text-content-primary outline-none placeholder:text-content-muted"
        />
        {pubs.query && (
          <button
            type="button"
            onClick={() => pubs.setQuery("")}
            className="shrink-0 text-xs uppercase tracking-wider text-content-muted hover:text-content-primary"
          >
            Clear
          </button>
        )}
      </div>

      {pubs.status === "loading" && pubs.results.length === 0 && (
        <div className="flex flex-col gap-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} height={88} />
          ))}
        </div>
      )}

      {pubs.status === "unavailable" && (
        <div className="glass hairline p-10 text-center text-sm text-content-secondary">
          Publication records are served from the database. Connect the backend to
          browse stored PubMed literature.
        </div>
      )}

      {pubs.status === "error" && (
        <div className="glass hairline border-state-danger/40 p-10 text-center text-sm text-state-danger">
          Publications could not be loaded. Please try again.
        </div>
      )}

      {pubs.status === "success" && pubs.results.length === 0 && (
        <div className="glass hairline p-10 text-center text-sm text-content-secondary">
          {pubs.query.trim()
            ? `No publications in the database match “${pubs.query.trim()}”. Nothing is shown that does not exist.`
            : "The database is connected but no publication records have been imported yet."}
        </div>
      )}

      {pubs.results.length > 0 && (
        <div className="flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <span className="eyebrow">Stored literature · real records</span>
            <span className="font-mono text-[11px] text-content-muted">
              {formatStatistic(pubs.total)}
            </span>
          </div>
          {pubs.results.map((publication) => (
            <PublicationRow key={publication.id} publication={publication} />
          ))}
          <div className="flex flex-col items-center justify-between gap-3 sm:flex-row">
            <span className="font-mono text-xs text-content-muted">
              Showing {from}–{to}
              {pubs.total > 0 ? ` of ${formatStatistic(pubs.total)}` : ""}
            </span>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={pubs.prevPage} disabled={!pubs.canPrev}>
                Previous
              </Button>
              <span className="px-2 font-mono text-xs text-content-secondary">
                Page {pubs.pageIndex + 1}
              </span>
              <Button variant="outline" size="sm" onClick={pubs.nextPage} disabled={!pubs.canNext}>
                Next
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
