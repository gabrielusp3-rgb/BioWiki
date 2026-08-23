"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useDebouncedValue } from "@/hooks/useDebouncedValue";
import { listCrispr } from "@/services/crisprService";
import { isApiConfigured } from "@/lib/api";
import { DEFAULT_CRISPR_FILTERS, type CrisprFilters, type CrisprGuide } from "@/types/crispr";

export type CrisprStatus = "idle" | "loading" | "success" | "error" | "unavailable";

const PAGE_SIZE = 20;

export function useCrispr() {
  const [query, setQuery] = useState("");
  const [filters, setFilters] = useState<CrisprFilters>(DEFAULT_CRISPR_FILTERS);
  const [status, setStatus] = useState<CrisprStatus>(isApiConfigured ? "idle" : "unavailable");
  const [results, setResults] = useState<CrisprGuide[]>([]);
  const [total, setTotal] = useState(0);

  const [cursors, setCursors] = useState<(string | null)[]>([null]);
  const [pageIndex, setPageIndex] = useState(0);
  const [nextCursor, setNextCursor] = useState<string | null>(null);

  const debouncedQuery = useDebouncedValue(query, 300);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    setCursors([null]);
    setPageIndex(0);
  }, [debouncedQuery, filters]);

  useEffect(() => {
    if (!isApiConfigured) {
      setStatus("unavailable");
      setResults([]);
      setTotal(0);
      setNextCursor(null);
      return;
    }

    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    setStatus("loading");

    listCrispr(debouncedQuery, filters, {
      limit: PAGE_SIZE,
      cursor: cursors[pageIndex] ?? undefined,
      signal: controller.signal,
    })
      .then((response) => {
        if (controller.signal.aborted) return;
        setResults(response.results);
        setTotal(response.total);
        setNextCursor(response.nextCursor);
        setStatus("success");
      })
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        if (error instanceof DOMException && error.name === "AbortError") return;
        setStatus("error");
        setResults([]);
        setTotal(0);
        setNextCursor(null);
      });

    return () => controller.abort();
  }, [debouncedQuery, filters, cursors, pageIndex]);

  const canPrev = pageIndex > 0;
  const canNext = nextCursor !== null;

  const nextPage = useCallback(() => {
    if (!nextCursor) return;
    setCursors((prev) => [...prev.slice(0, pageIndex + 1), nextCursor]);
    setPageIndex((i) => i + 1);
  }, [nextCursor, pageIndex]);

  const prevPage = useCallback(() => setPageIndex((i) => Math.max(0, i - 1)), []);
  const resetFilters = useCallback(() => setFilters(DEFAULT_CRISPR_FILTERS), []);

  const activeFilterCount = useMemo(() => {
    let count = 0;
    if (filters.organism) count += 1;
    if (filters.source !== "all") count += 1;
    if (filters.system !== "all") count += 1;
    if (filters.targetGene) count += 1;
    if (filters.pam) count += 1;
    if (filters.minLength !== null) count += 1;
    if (filters.maxLength !== null) count += 1;
    return count;
  }, [filters]);

  return {
    query,
    setQuery,
    filters,
    setFilters,
    resetFilters,
    activeFilterCount,
    status,
    results,
    total,
    pageIndex,
    pageSize: PAGE_SIZE,
    canPrev,
    canNext,
    nextPage,
    prevPage,
  };
}
