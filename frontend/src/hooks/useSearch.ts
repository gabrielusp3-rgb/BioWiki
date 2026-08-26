"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useDebouncedValue } from "@/hooks/useDebouncedValue";
import { search, suggest } from "@/services/searchService";
import { isApiConfigured, readNextCursor } from "@/lib/api";
import {
  DEFAULT_FILTERS,
  type SearchFilters,
  type SearchPublication,
  type SearchResult,
  type SearchSuggestion,
} from "@/types/search";

export type SearchStatus = "idle" | "loading" | "success" | "error" | "unavailable";

interface UseSearchOptions {
  debounceMs?: number;
  minChars?: number;
  initialQuery?: string;
}

export function useSearch({
  debounceMs = 250,
  minChars = 2,
  initialQuery = "",
}: UseSearchOptions = {}) {
  const [query, setQuery] = useState(initialQuery);
  const [filters, setFilters] = useState<SearchFilters>(DEFAULT_FILTERS);
  const [status, setStatus] = useState<SearchStatus>("idle");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [suggestions, setSuggestions] = useState<SearchSuggestion[]>([]);
  const [publications, setPublications] = useState<SearchPublication[]>([]);
  const [publicationsTotal, setPublicationsTotal] = useState(0);
  const [total, setTotal] = useState(0);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [loadingMore, setLoadingMore] = useState(false);

  const debouncedQuery = useDebouncedValue(query, debounceMs);
  const abortRef = useRef<AbortController | null>(null);

  const activeFilterCount = useMemo(() => {
    let count = filters.types.length;
    if (filters.organism) count += 1;
    if (filters.source !== "all") count += 1;
    if (filters.category !== "all") count += 1;
    if (filters.minLength !== null) count += 1;
    if (filters.maxLength !== null) count += 1;
    if (filters.complexity !== "any") count += 1;
    return count;
  }, [filters]);

  useEffect(() => {
    const trimmed = debouncedQuery.trim();

    abortRef.current?.abort();

    if (trimmed.length < minChars) {
      setStatus("idle");
      setResults([]);
      setSuggestions([]);
      setPublications([]);
      setPublicationsTotal(0);
      setTotal(0);
      setNextCursor(null);
      return;
    }

    if (!isApiConfigured) {
      setStatus("unavailable");
      setResults([]);
      setSuggestions([]);
      setPublications([]);
      setPublicationsTotal(0);
      setTotal(0);
      setNextCursor(null);
      return;
    }

    const controller = new AbortController();
    abortRef.current = controller;
    setStatus("loading");

    Promise.all([
      search(trimmed, filters, { signal: controller.signal }),
      suggest(trimmed, { signal: controller.signal }),
    ])
      .then(([searchResponse, suggestResponse]) => {
        if (controller.signal.aborted) return;
        setResults(searchResponse.results);
        setTotal(searchResponse.total);
        setNextCursor(readNextCursor(searchResponse));
        setPublications(searchResponse.publications ?? []);
        setPublicationsTotal(searchResponse.publicationsTotal ?? 0);
        setSuggestions(suggestResponse.suggestions);
        setStatus("success");
      })
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        if (error instanceof DOMException && error.name === "AbortError") return;
        setStatus("error");
        setResults([]);
        setSuggestions([]);
        setPublications([]);
        setPublicationsTotal(0);
        setTotal(0);
        setNextCursor(null);
      });

    return () => controller.abort();
  }, [debouncedQuery, filters, minChars]);

  const resetFilters = useCallback(() => setFilters(DEFAULT_FILTERS), []);

  /** Fetch the next page (cursor pagination) and append it to the results. */
  const loadMore = useCallback(async () => {
    const trimmed = debouncedQuery.trim();
    if (!nextCursor || !trimmed || loadingMore || !isApiConfigured) return;
    setLoadingMore(true);
    try {
      const page = await search(trimmed, filters, { cursor: nextCursor });
      setResults((prev) => [...prev, ...page.results]);
      setNextCursor(readNextCursor(page));
      setTotal(page.total);
    } catch {
      // Keep the already-loaded results; the button stays available for retry.
    } finally {
      setLoadingMore(false);
    }
  }, [debouncedQuery, filters, nextCursor, loadingMore]);

  return {
    query,
    setQuery,
    filters,
    setFilters,
    resetFilters,
    activeFilterCount,
    status,
    results,
    suggestions,
    publications,
    publicationsTotal,
    total,
    nextCursor,
    loadMore,
    loadingMore,
  };
}
