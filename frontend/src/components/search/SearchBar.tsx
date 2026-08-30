"use client";

import { useEffect, useId, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";
import { cn } from "@/lib/cn";
import { Badge, Skeleton, Tag } from "@/components/ui";
import { SearchIcon, ChevronRightIcon } from "@/components/ui/Icons";
import { SearchFilters } from "@/components/search/SearchFilters";
import { useSearch } from "@/hooks/useSearch";
import { SEARCH_TYPES } from "@/lib/search-config";
import { CATEGORY_META } from "@/lib/categories";
import { formatStatistic } from "@/lib/statistics";
import { pathForSearchType, searchUrl } from "@/lib/search-routes";
import type { SearchPaleogenomicsProfile, SearchResult, SearchSuggestion, SearchType } from "@/types/search";

function PaleoRow({
  profile,
  onNavigate,
}: {
  profile: Pick<SearchPaleogenomicsProfile, "slug" | "title" | "scientificName">;
  onNavigate: () => void;
}) {
  return (
    <Link
      href={`/paleogenomics/${encodeURIComponent(profile.slug)}`}
      onClick={onNavigate}
      className="flex w-full items-center gap-4 border-b border-glass-divider/60 px-4 py-3 text-left transition-colors hover:bg-white/[0.04]"
    >
      <span className="shrink-0 font-display text-[10px] uppercase tracking-wider text-content-muted">
        Paleo
      </span>
      <span className="flex min-w-0 flex-1 flex-col">
        <span className="truncate font-body text-sm text-content-primary">{profile.title}</span>
        <span className="truncate text-xs italic text-content-secondary">{profile.scientificName}</span>
      </span>
    </Link>
  );
}

function ResultRow({ result, onNavigate }: { result: SearchResult; onNavigate: () => void }) {
  return (
    <Link
      href={`/sequences/${encodeURIComponent(result.accession)}`}
      onClick={onNavigate}
      className="flex w-full items-center gap-4 border-b border-glass-divider/60 px-4 py-3 text-left transition-colors hover:bg-white/[0.04]"
    >
      <Badge category={result.category} />
      <span className="flex min-w-0 flex-1 flex-col">
        <span className="truncate font-body text-sm text-content-primary">{result.title}</span>
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

function IntentRow({
  label,
  type,
  query,
  onNavigate,
}: {
  label: string;
  type: SearchType;
  query: string;
  onNavigate: () => void;
}) {
  const meta = SEARCH_TYPES.find((t) => t.type === type);
  const color = meta?.category ? CATEGORY_META[meta.category].color : "#8A8A8A";
  return (
    <Link
      href={searchUrl(pathForSearchType(type), query)}
      onClick={onNavigate}
      className="flex w-full items-center gap-3 px-4 py-2.5 text-left transition-colors hover:bg-white/[0.04]"
    >
      <span className="h-1.5 w-1.5 shrink-0" style={{ backgroundColor: color }} />
      <span className="flex-1 truncate text-sm text-content-secondary">
        Search <span className="text-content-primary">“{query}”</span> in {label}
      </span>
      <ChevronRightIcon className="h-4 w-4 text-content-muted" />
    </Link>
  );
}

export interface SearchBarProps {
  /** Pre-fills the query (e.g. from a `?q=` deep link) and opens the dropdown. */
  initialQuery?: string;
}

export function SearchBar({ initialQuery = "" }: SearchBarProps = {}) {
  const {
    query,
    setQuery,
    filters,
    setFilters,
    resetFilters,
    activeFilterCount,
    status,
    results,
    suggestions,
    paleogenomicsProfiles,
    total,
  } = useSearch({ initialQuery });

  const [open, setOpen] = useState(Boolean(initialQuery.trim()));
  const [showFilters, setShowFilters] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const listId = useId();
  const router = useRouter();

  const submitQuery = () => {
    const trimmed = query.trim();
    if (!trimmed) return;
    setOpen(false);
    router.push(searchUrl("/search", trimmed));
  };

  useEffect(() => {
    const onPointerDown = (event: PointerEvent) => {
      if (!containerRef.current?.contains(event.target as Node)) setOpen(false);
    };
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "/" && document.activeElement !== inputRef.current) {
        event.preventDefault();
        inputRef.current?.focus();
      }
      if (event.key === "Escape") setOpen(false);
    };
    window.addEventListener("pointerdown", onPointerDown);
    window.addEventListener("keydown", onKey);
    return () => {
      window.removeEventListener("pointerdown", onPointerDown);
      window.removeEventListener("keydown", onKey);
    };
  }, []);

  const hasQuery = query.trim().length >= 2;
  const showDropdown = open && hasQuery;

  return (
    <div ref={containerRef} className="relative w-full">
      {/* Input */}
      <div
        className={cn(
          "glass hairline flex items-center gap-3 px-4 transition-colors duration-200",
          open ? "border-category-dna/50" : "border-glass-border",
        )}
      >
        <SearchIcon className="h-5 w-5 shrink-0 text-content-secondary" />
        <input
          ref={inputRef}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => setOpen(true)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              submitQuery();
            }
          }}
          role="combobox"
          aria-expanded={showDropdown}
          aria-controls={listId}
          aria-autocomplete="list"
          placeholder="Search genes, proteins, accessions, organisms, taxonomy…"
          className="h-16 w-full bg-transparent font-body text-base text-content-primary outline-none placeholder:text-content-muted"
        />
        {query && (
          <button
            type="button"
            onClick={() => {
              setQuery("");
              inputRef.current?.focus();
            }}
            className="shrink-0 text-xs uppercase tracking-wider text-content-muted hover:text-content-primary"
          >
            Clear
          </button>
        )}
        <span className="hidden shrink-0 border border-glass-border px-2 py-1 font-mono text-[11px] text-content-muted sm:block">
          /
        </span>
        <button
          type="button"
          onClick={() => setShowFilters((v) => !v)}
          className={cn(
            "shrink-0 border px-3 py-2 font-display text-xs font-semibold uppercase tracking-wide transition-colors",
            showFilters || activeFilterCount > 0
              ? "border-category-dna/50 text-category-dna"
              : "border-glass-border text-content-secondary hover:text-content-primary",
          )}
        >
          Filters{activeFilterCount > 0 ? ` · ${activeFilterCount}` : ""}
        </button>
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

      {/* Autocomplete dropdown */}
      <AnimatePresence>
        {showDropdown && (
          <motion.div
            id={listId}
            role="listbox"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 8 }}
            transition={{ duration: 0.18, ease: [0.22, 1, 0.36, 1] }}
            className="glass-strong absolute inset-x-0 top-full z-[300] mt-2 max-h-[60vh] overflow-y-auto"
          >
            {status === "loading" && (
              <div className="flex flex-col gap-2 p-4">
                <Skeleton height={44} />
                <Skeleton height={44} />
                <Skeleton height={44} />
              </div>
            )}

            {status === "success" && paleogenomicsProfiles.length > 0 && (
              <>
                <span className="eyebrow block px-4 pt-4">Paleogenomics</span>
                <div className="mt-2">
                  {paleogenomicsProfiles.map((profile) => (
                    <PaleoRow
                      key={profile.id}
                      profile={profile}
                      onNavigate={() => setOpen(false)}
                    />
                  ))}
                </div>
              </>
            )}

            {status === "success" && results.length > 0 && (
              <>
                <div className="flex items-center justify-between px-4 pt-4">
                  <span className="eyebrow">Results</span>
                  <span className="font-mono text-[11px] text-content-muted">
                    {formatStatistic(total)} total
                  </span>
                </div>
                <div className="mt-2">
                  {results.map((result) => (
                    <ResultRow key={result.id} result={result} onNavigate={() => setOpen(false)} />
                  ))}
                </div>
              </>
            )}

            {status === "success" && suggestions.length > 0 && (
              <>
                <span className="eyebrow block px-4 pt-4">Suggestions</span>
                <div className="mb-2 mt-2">
                  {suggestions.map((s: SearchSuggestion) =>
                    s.type === "paleogenomics" && s.slug ? (
                      <PaleoRow
                        key={s.id}
                        profile={{
                          slug: s.slug,
                          title: s.label,
                          scientificName: s.label,
                        }}
                        onNavigate={() => setOpen(false)}
                      />
                    ) : (
                      <IntentRow
                        key={s.id}
                        label={s.label}
                        type={s.type as SearchType}
                        query={s.label}
                        onNavigate={() => setOpen(false)}
                      />
                    ),
                  )}
                </div>
              </>
            )}

            {status === "success" &&
              results.length === 0 &&
              suggestions.length === 0 &&
              paleogenomicsProfiles.length === 0 && (
              <div className="p-8 text-center text-sm text-content-secondary">
                No matches found in the database for “{query.trim()}”.
              </div>
            )}

            {status === "unavailable" && (
              <>
                <div className="border-b border-glass-divider p-4 text-sm text-content-secondary">
                  Live results appear once the sequence database is connected. You can
                  still choose where to search:
                </div>
                <div className="py-2">
                  {SEARCH_TYPES.map((meta) => (
                    <IntentRow
                      key={meta.type}
                      label={meta.label}
                      type={meta.type}
                      query={query.trim()}
                      onNavigate={() => setOpen(false)}
                    />
                  ))}
                </div>
              </>
            )}

            {status === "error" && (
              <div className="p-8 text-center text-sm text-state-danger">
                Search is temporarily unavailable. Please try again.
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Filters panel */}
      <AnimatePresence>
        {showFilters && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.24, ease: [0.22, 1, 0.36, 1] }}
            className="overflow-hidden"
          >
            <div className="mt-4">
              <SearchFilters filters={filters} onChange={setFilters} onReset={resetFilters} />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
