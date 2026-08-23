"use client";

import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { suggest } from "@/services/searchService";
import type { SearchSuggestion } from "@/types";
import { categoryColor } from "@/lib/categories";

export function SearchBox({ autoFocus = false }: { autoFocus?: boolean }) {
  const router = useRouter();
  const [q, setQ] = useState("");
  const [items, setItems] = useState<SearchSuggestion[]>([]);
  const [open, setOpen] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (timer.current) clearTimeout(timer.current);
    if (q.trim().length < 2) {
      setItems([]);
      return;
    }
    timer.current = setTimeout(() => {
      suggest(q.trim(), { limit: 8 })
        .then((r) => {
          setItems(r.suggestions);
          setOpen(true);
        })
        .catch(() => setItems([]));
    }, 200);
    return () => {
      if (timer.current) clearTimeout(timer.current);
    };
  }, [q]);

  const submit = () => {
    if (q.trim()) router.push(`/search?q=${encodeURIComponent(q.trim())}`);
  };

  return (
    <div className="relative w-full">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          submit();
        }}
        className="glass flex items-center gap-3 px-5 py-4"
      >
        <span className="text-neutral-500">⌕</span>
        <input
          autoFocus={autoFocus}
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onFocus={() => items.length && setOpen(true)}
          onBlur={() => setTimeout(() => setOpen(false), 150)}
          placeholder="Search sequences, genes, accessions, organisms, publications…"
          className="w-full bg-transparent text-sm text-white placeholder:text-neutral-600 focus:outline-none"
        />
        <button
          type="submit"
          className="bg-dna px-4 py-2 text-[0.65rem] font-semibold uppercase tracking-widest text-black"
        >
          Search
        </button>
      </form>

      {open && items.length > 0 && (
        <div className="glass absolute z-20 mt-1 max-h-80 w-full overflow-auto">
          {items.map((s) => (
            <button
              key={s.id}
              onMouseDown={() =>
                router.push(`/sequences/${encodeURIComponent(s.accession ?? "")}`)
              }
              className="flex w-full items-center justify-between gap-4 border-b border-white/5 px-5 py-3 text-left hover:bg-white/5"
            >
              <span className="truncate text-sm text-neutral-200">{s.label}</span>
              <span
                className="shrink-0 text-[0.6rem] font-semibold uppercase tracking-widest"
                style={{ color: categoryColor(s.type) }}
              >
                {s.type}
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
