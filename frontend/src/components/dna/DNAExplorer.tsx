"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { cn } from "@/lib/cn";
import { DNAFilters } from "@/components/dna/DNAFilters";
import { DNATable } from "@/components/dna/DNATable";
import { DNAViewer } from "@/components/dna/DNAViewer";
import { SearchIcon } from "@/components/ui/Icons";
import { useDnaSequences } from "@/hooks/useDnaSequences";
import { useQueryParamSync } from "@/hooks/useQueryParamSync";
import { getDna } from "@/services/dnaService";
import { downloadText, toFasta, toJson } from "@/lib/dna";
import type { DnaSequence } from "@/types/dna";

export function DNAExplorer() {
  const dna = useDnaSequences();
  useQueryParamSync(dna.setQuery);
  const [showFilters, setShowFilters] = useState(false);
  const [selected, setSelected] = useState<DnaSequence | null>(null);
  const [viewerOpen, setViewerOpen] = useState(false);

  const openViewer = (seq: DnaSequence) => {
    setSelected(seq);
    setViewerOpen(true);
  };

  const handleDownload = async (seq: DnaSequence) => {
    let full: DnaSequence | null = seq;
    if (!seq.sequence) {
      try {
        full = (await getDna(seq.accession)) ?? seq;
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
      {/* Search */}
      <div
        className={cn(
          "glass hairline flex items-center gap-3 px-4 transition-colors duration-200",
          "focus-within:border-category-dna/50",
        )}
      >
        <SearchIcon className="h-5 w-5 shrink-0 text-content-secondary" />
        <input
          value={dna.query}
          onChange={(e) => dna.setQuery(e.target.value)}
          placeholder="Search DNA by gene, accession, definition or organism…"
          className="h-14 w-full bg-transparent font-body text-base text-content-primary outline-none placeholder:text-content-muted"
        />
        {dna.query && (
          <button
            type="button"
            onClick={() => dna.setQuery("")}
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
            showFilters || dna.activeFilterCount > 0
              ? "border-category-dna/50 text-category-dna"
              : "border-glass-border text-content-secondary hover:text-content-primary",
          )}
        >
          Filters{dna.activeFilterCount > 0 ? ` · ${dna.activeFilterCount}` : ""}
        </button>
      </div>

      {/* Filters */}
      <AnimatePresence>
        {showFilters && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.24, ease: [0.22, 1, 0.36, 1] }}
            className="overflow-hidden"
          >
            <DNAFilters
              filters={dna.filters}
              onChange={dna.setFilters}
              onReset={dna.resetFilters}
            />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Table + pagination */}
      <DNATable
        results={dna.results}
        status={dna.status}
        total={dna.total}
        pageIndex={dna.pageIndex}
        pageSize={dna.pageSize}
        canPrev={dna.canPrev}
        canNext={dna.canNext}
        onPrev={dna.prevPage}
        onNext={dna.nextPage}
        onView={openViewer}
        onDownload={handleDownload}
      />

      {/* Viewer */}
      <DNAViewer sequence={selected} open={viewerOpen} onClose={() => setViewerOpen(false)} />
    </div>
  );
}
