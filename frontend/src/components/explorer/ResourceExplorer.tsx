"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { Section } from "@/components/ui/Container";
import { Badge } from "@/components/ui/Badge";
import { formatNumber, formatBases } from "@/lib/format";
import { readNextCursor } from "@/lib/api";

export interface Row {
  key: string;
  href: string;
  accession: string;
  name: string;
  organism: string;
  source: string;
  length: number;
  lengthLabel?: string;
  tags: { label: string; color?: string }[];
}

export interface Page {
  results: unknown[];
  total: number;
  nextCursor?: string | null;
}

export function ResourceExplorer({
  eyebrow,
  title,
  description,
  color,
  fetchPage,
  mapRow,
}: {
  eyebrow: string;
  title: string;
  description: string;
  color: string;
  fetchPage: (params: {
    q?: string;
    cursor?: string | null;
  }) => Promise<Page>;
  mapRow: (item: unknown) => Row;
}) {
  const [rows, setRows] = useState<Row[]>([]);
  const [total, setTotal] = useState<number | null>(null);
  const [cursor, setCursor] = useState<string | null>(null);
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const query = useRef("");

  const load = useCallback(
    async (reset: boolean) => {
      setLoading(true);
      setError(false);
      try {
        const page = await fetchPage({
          q: query.current || undefined,
          cursor: reset ? null : cursor,
        });
        const mapped = page.results.map(mapRow);
        setRows((prev) => (reset ? mapped : [...prev, ...mapped]));
        setTotal(page.total);
        setCursor(readNextCursor(page));
      } catch {
        setError(true);
      } finally {
        setLoading(false);
      }
    },
    [cursor, fetchPage, mapRow],
  );

  useEffect(() => {
    query.current = "";
    load(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const runSearch = () => {
    query.current = q.trim();
    setCursor(null);
    load(true);
  };

  return (
    <Section
      eyebrow={eyebrow}
      title={title}
      description={description}
      action={
        <span className="display text-3xl" style={{ color }}>
          {total === null ? "…" : formatNumber(total)}
        </span>
      }
    >
      <form
        onSubmit={(e) => {
          e.preventDefault();
          runSearch();
        }}
        className="glass mb-6 flex items-center gap-3 px-5 py-3"
      >
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Filter by name, accession or gene…"
          className="w-full bg-transparent text-sm text-white placeholder:text-neutral-600 focus:outline-none"
        />
        <button
          type="submit"
          className="px-4 py-2 text-[0.65rem] font-semibold uppercase tracking-widest text-black"
          style={{ background: color }}
        >
          Filter
        </button>
      </form>

      {error && (
        <p className="text-xs uppercase tracking-widest text-virus">
          Could not load records — is the API running?
        </p>
      )}

      {!error && total === 0 && !loading && (
        <p className="glass p-8 text-sm text-neutral-400">
          No records stored for this category yet.
        </p>
      )}

      <div className="flex flex-col gap-px bg-white/5">
        {rows.map((r) => (
          <Link
            key={r.key}
            href={r.href}
            className="glass glass-hover flex flex-col gap-3 p-5 md:flex-row md:items-center md:justify-between"
          >
            <div className="min-w-0">
              <div className="flex items-center gap-3">
                <span className="font-mono text-sm" style={{ color }}>
                  {r.accession}
                </span>
                {r.tags.map((t) => (
                  <Badge key={t.label} style={t.color ? { color: t.color } : undefined}>
                    {t.label}
                  </Badge>
                ))}
              </div>
              <p className="mt-1 truncate text-sm text-neutral-200">{r.name}</p>
              <p className="text-xs italic text-neutral-500">{r.organism}</p>
            </div>
            <div className="flex shrink-0 items-center gap-8 text-right">
              <div>
                <p className="text-sm text-white">
                  {r.lengthLabel ?? formatBases(r.length)}
                </p>
                <p className="text-[0.65rem] uppercase tracking-widest text-neutral-600">
                  {r.source}
                </p>
              </div>
            </div>
          </Link>
        ))}
      </div>

      {cursor && !loading && (
        <div className="mt-8 flex justify-center">
          <button
            onClick={() => load(false)}
            className="glass glass-hover px-6 py-3 text-[0.65rem] font-semibold uppercase tracking-widest text-white"
          >
            Load more
          </button>
        </div>
      )}
      {loading && (
        <p className="mt-8 text-center text-xs uppercase tracking-widest text-neutral-600">
          Loading…
        </p>
      )}
    </Section>
  );
}
