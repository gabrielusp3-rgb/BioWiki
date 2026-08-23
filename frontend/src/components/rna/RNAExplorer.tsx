"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { cn } from "@/lib/cn";
import { RNAFilters } from "@/components/rna/RNAFilters";
import { RNATable } from "@/components/rna/RNATable";
import { RNAViewer } from "@/components/rna/RNAViewer";
import { SearchIcon } from "@/components/ui/Icons";
import { useRnaSequences } from "@/hooks/useRnaSequences";
import { useQueryParamSync } from "@/hooks/useQueryParamSync";
import { getRna } from "@/services/rnaService";
import { downloadText, toFasta, toJson } from "@/lib/rna";
import type { RnaSequence } from "@/types/rna";

export function RNAExplorer() {
  const rna = useRnaSequences();
  useQueryParamSync(rna.setQuery);
  const [showFilters, setShowFilters] = useState(false);
  const [selected, setSelected] = useState<RnaSequence | null>(null);
  const [viewerOpen, setViewerOpen] = useState(false);

  const openViewer = (seq: RnaSequence) => {
    setSelected(seq);
    setViewerOpen(true);
  };

  const handleDownload = async (seq: RnaSequence) => {
    let full: RnaSequence | null = seq;
    if (!seq.sequence) {
      try {
        full = (await getRna(seq.accession)) ?? seq;
      } catch {
        full = seq;
      }
    }
    if (full.sequence) {
      downloadText(`${full.accession}.fasta`, toFasta(full), "text/plain");
    } else {
      downloadText(`${full.accession}.json`, toJson(full), "application/json");
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <div
        className={cn(
          "glass hairline flex items-center gap-3 px-4 transition-colors duration-200",
          "focus-within:border-category-rna/50",
        )}
      >
        <SearchIcon className="h-5 w-5 shrink-0 text-content-secondary" />
        <input
          value={rna.query}
          onChange={(e) => rna.setQuery(e.target.value)}
          placeholder="Search RNA by gene, accession, definition or organism…"
          className="h-14 w-full bg-transparent font-body text-base text-content-primary outline-none placeholder:text-content-muted"
        />
        {rna.query && (
          <button
            type="button"
            onClick={() => rna.setQuery("")}
            className="shrink-0 text-xs uppercase tracking-wider text-content-muted hover:text-content-primary"
          >
            Clear
          </button>
        )}
        <button
          type="button"
          onClick={() => setShowFilters((v) => !v)}
          className={cn(
            "shrink-0 border px-3 py-2 font-display text-xs font-semibold uppercase tracking-wide transition-colors",
            showFilters || rna.activeFilterCount > 0
              ? "border-category-rna/50 text-category-rna"
              : "border-glass-border text-content-secondary hover:text-content-primary",
          )}
        >
          Filters{rna.activeFilterCount > 0 ? ` · ${rna.activeFilterCount}` : ""}
        </button>
      </div>

      <AnimatePresence>
        {showFilters && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.24, ease: [0.22, 1, 0.36, 1] }}
            className="overflow-hidden"
          >
            <RNAFilters
              filters={rna.filters}
              onChange={rna.setFilters}
              onReset={rna.resetFilters}
            />
          </motion.div>
        )}
      </AnimatePresence>

      <RNATable
        results={rna.results}
        status={rna.status}
        total={rna.total}
        pageIndex={rna.pageIndex}
        pageSize={rna.pageSize}
        canPrev={rna.canPrev}
        canNext={rna.canNext}
        onPrev={rna.prevPage}
        onNext={rna.nextPage}
        onView={openViewer}
        onDownload={handleDownload}
      />

      <RNAViewer sequence={selected} open={viewerOpen} onClose={() => setViewerOpen(false)} />
    </div>
  );
}
