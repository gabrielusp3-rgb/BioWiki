"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useDebouncedValue } from "@/hooks/useDebouncedValue";
import { isApiConfigured } from "@/lib/api";
import { listPublications } from "@/services/publicationService";
import type { Publication } from "@/types/publication";

export type PublicationStatus = "idle" | "loading" | "success" | "error" | "unavailable";

const PAGE_SIZE = 20;

export function usePublications() {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState<PublicationStatus>(isApiConfigured ? "idle" : "unavailable");
  const [results, setResults] = useState<Publication[]>([]);
  const [total, setTotal] = useState(0);
  const [cursors, setCursors] = useState<(string | null)[]>([null]);
  const [pageIndex, setPageIndex] = useState(0);
  const [nextCursor, setNextCursor] = useState<string | null>(null);

  const debouncedQuery = useDebouncedValue(query, 300);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    setCursors([null]);
    setPageIndex(0);
  }, [debouncedQuery]);

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

    listPublications({
      q: debouncedQuery.trim() || undefined,
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
  }, [debouncedQuery, cursors, pageIndex]);

  const nextPage = useCallback(() => {
    if (!nextCursor) return;
    setCursors((prev) => {
      const trimmed = prev.slice(0, pageIndex + 1);
      return [...trimmed, nextCursor];
    });
    setPageIndex((i) => i + 1);
  }, [nextCursor, pageIndex]);

  const prevPage = useCallback(() => {
    setPageIndex((i) => Math.max(0, i - 1));
  }, []);

  return {
    query,
    setQuery,
    status,
    results,
    total,
    pageIndex,
    pageSize: PAGE_SIZE,
    canPrev: pageIndex > 0,
    canNext: nextCursor !== null,
    nextPage,
    prevPage,
  };
}
