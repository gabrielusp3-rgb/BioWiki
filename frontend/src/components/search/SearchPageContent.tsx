"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import { Badge, Button, Skeleton, Tag } from "@/components/ui";
import { ExternalIcon, SearchIcon } from "@/components/ui/Icons";
import { SearchFilters } from "@/components/search/SearchFilters";
import { useSearch } from "@/hooks/useSearch";
import { fadeInUp, staggerContainer } from "@/lib/animations";
import { SEARCH_TYPES } from "@/lib/search-config";
import { formatStatistic } from "@/lib/statistics";
import type { SearchPublication, SearchResult } from "@/types/search";

function ResultRow({ result }: { result: SearchResult }) {
  return (
    <Link
      href={`/sequences/${encodeURIComponent(result.accession)}`}
      className="glass hairline group flex w-full items-center gap-4 px-5 py-4 transition-colors hover:border-white/20"
    >
      <Badge category={result.category} />
      <span className="flex min-w-0 flex-1 flex-col">
        <span className="truncate font-body text-sm text-content-primary">
          {result.title}
        </span>
        <span className="truncate text-xs text-content-secondary">
          {result.organism} · {result.source}
        </span>
      </span>
      <span className="hidden shrink-0 font-mono text-xs text-content-secondary sm:block">
        {result.accession}
      </span>
      <span className="shrink-0 font-mono text-[11px] text-content-muted">
        {formatStatistic(result.length)} bp
      </span>
    </Link>
  );
}

function PublicationRow({ publication }: { publication: SearchPublication }) {
  const authors =
    publication.authors.length > 3
      ? `${publication.authors.slice(0, 3).join(", ")} et al.`
      : publication.authors.join(", ");
  const href = publication.pubmedId
    ? `/publications/${publication.pubmedId}`
    : (publication.url ?? "#");
  return (
    <Link
      href={href}
      className="glass hairline group flex w-full items-start gap-4 px-5 py-4 transition-colors hover:border-white/20"
    >
      <span className="flex min-w-0 flex-1 flex-col gap-1">
        <span className="font-body text-sm text-content-primary">
          {publication.title}
        </span>
        <span className="truncate text-xs text-content-secondary">
          {[authors, publication.journal, publication.year]
            .filter(Boolean)
            .join(" · ")}
        </span>
      </span>
      {publication.pubmedId && (
        <span className="shrink-0 font-mono text-[11px] text-content-muted">
          PMID {publication.pubmedId}
        </span>
      )}
      <ExternalIcon className="mt-0.5 h-4 w-4 shrink-0 text-content-muted group-hover:text-content-primary" />
    </Link>
  );
}

export function SearchPageContent() {
  const searchParams = useSearchParams();
  const initialQuery = searchParams.get("q") ?? "";

  const {
    query,
    setQuery,
    filters,
    setFilters,
    resetFilters,
    activeFilterCount,
    status,
    results,
    publications,
    publicationsTotal,
    total,
    nextCursor,
    loadMore,
    loadingMore,
  } = useSearch({ initialQuery, minChars: 2 });

  const trimmed = query.trim();
  const hasQuery = trimmed.length >= 2;

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-8">
      {/* Query input */}
      <div>
        <div className="glass hairline flex items-center gap-3 px-4">
          <SearchIcon className="h-5 w-5 shrink-0 text-content-secondary" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search accessions, genes, organisms, tax IDs, publications…"
            autoFocus
            className="h-16 w-full bg-transparent font-body text-base text-content-primary outline-none placeholder:text-content-muted"
          />
          {query && (
            <button
              type="button"
              onClick={() => setQuery("")}
              className="shrink-0 text-xs uppercase tracking-wider text-content-muted hover:text-content-primary"
            >
              Clear
            </button>
          )}
        </div>

        {/* Scope tags */}
        <div className="mt-3 flex flex-wrap gap-2">
          {SEARCH_TYPES.map((meta) => (
            <Tag
              key={meta.type}
              active={filters.types.includes(meta.type)}
              onClick={() =>
                setFilters({
                  ...filters,
                  types: filters.types.includes(meta.type)
                    ? filters.types.filter((t) => t !== meta.type)
                    : [...filters.types, meta.type],
                })
              }
            >
              {meta.label}
            </Tag>
          ))}
        </div>

        <div className="mt-4">
          <SearchFilters filters={filters} onChange={setFilters} onReset={resetFilters} />
        </div>
        {activeFilterCount > 0 && (
          <p className="mt-2 text-xs text-content-muted">
            {activeFilterCount} active filter{activeFilterCount > 1 ? "s" : ""}
          </p>
        )}
      </div>

      {/* States */}
      {!hasQuery && status === "idle" && (
        <div className="glass hairline p-10 text-center text-sm text-content-secondary">
          Type at least two characters to search the database — by accession,
          gene, organism, scientific name, NCBI tax ID, sequence type, length or
          free text. Publication search covers PMID, title and authors.
        </div>
      )}

      {status === "loading" && (
        <div className="flex flex-col gap-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} height={72} />
          ))}
        </div>
      )}

      {status === "unavailable" && (
        <div className="glass hairline p-10 text-center text-sm text-content-secondary">
          Live results appear once the sequence database is connected.
        </div>
      )}

      {status === "error" && (
        <div className="glass hairline border-state-danger/40 p-10 text-center text-sm text-state-danger">
          Search is temporarily unavailable. Please try again.
        </div>
      )}

      {status === "success" && results.length === 0 && publications.length === 0 && (
        <div className="glass hairline p-10 text-center text-sm text-content-secondary">
          No matches found in the database for “{trimmed}”. Nothing is shown
          that does not exist — try another accession, gene or organism.
        </div>
      )}

      {/* Sequence results */}
      {status === "success" && results.length > 0 && (
        <section>
          <div className="mb-3 flex items-center justify-between">
            <span className="eyebrow">Sequences</span>
            <span className="font-mono text-[11px] text-content-muted">
              {formatStatistic(total)} match{total === 1 ? "" : "es"} · ordered by relevance
            </span>
          </div>
          <motion.div
            variants={staggerContainer(0.04, 0)}
            initial="hidden"
            animate="visible"
            className="flex flex-col gap-3"
          >
            {results.map((result) => (
              <motion.div key={result.id} variants={fadeInUp}>
                <ResultRow result={result} />
              </motion.div>
            ))}
          </motion.div>
          {nextCursor && (
            <div className="mt-4 flex justify-center">
              <Button variant="glass" size="md" onClick={loadMore} disabled={loadingMore}>
                {loadingMore ? "Loading…" : "Load more results"}
              </Button>
            </div>
          )}
        </section>
      )}

      {/* Publication results */}
      {status === "success" && publications.length > 0 && (
        <section>
          <div className="mb-3 flex items-center justify-between">
            <span className="eyebrow">Publications</span>
            <span className="font-mono text-[11px] text-content-muted">
              {formatStatistic(publicationsTotal)} match{publicationsTotal === 1 ? "" : "es"} · PubMed
            </span>
          </div>
          <div className="flex flex-col gap-3">
            {publications.map((publication) => (
              <PublicationRow key={publication.id} publication={publication} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
