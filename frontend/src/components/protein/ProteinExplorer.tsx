"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { cn } from "@/lib/cn";
import { Button } from "@/components/ui";
import { SearchIcon } from "@/components/ui/Icons";
import { ProteinFilters } from "@/components/protein/ProteinFilters";
import { ProteinTable } from "@/components/protein/ProteinTable";
import { ProteinCard } from "@/components/protein/ProteinCard";
import { ProteinViewer } from "@/components/protein/ProteinViewer";
import { useProteins } from "@/hooks/useProteins";
import { useQueryParamSync } from "@/hooks/useQueryParamSync";
import { getProtein } from "@/services/proteinService";
import { downloadText, toFasta, toJson } from "@/lib/protein";
import type { ProteinSequence } from "@/types/protein";

type ViewMode = "table" | "cards";

export function ProteinExplorer() {
  const proteins = useProteins();
  useQueryParamSync(proteins.setQuery);
  const [showFilters, setShowFilters] = useState(false);
  const [view, setView] = useState<ViewMode>("table");
  const [selected, setSelected] = useState<ProteinSequence | null>(null);
  const [viewerOpen, setViewerOpen] = useState(false);

  const openViewer = (seq: ProteinSequence) => {
    setSelected(seq);
    setViewerOpen(true);
  };

  const handleDownload = async (seq: ProteinSequence) => {
    let full: ProteinSequence | null = seq;
    if (!seq.sequence) {
      try {
        full = (await getProtein(seq.accession)) ?? seq;
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

  const showCards = view === "cards" && proteins.status === "success" && proteins.results.length > 0;

  return (
    <div className="flex flex-col gap-6">
      <div
        className={cn(
          "glass hairline flex items-center gap-3 px-4 transition-colors duration-200",
          "focus-within:border-category-protein/50",
        )}
      >
        <SearchIcon className="h-5 w-5 shrink-0 text-content-secondary" />
        <input
          value={proteins.query}
          onChange={(e) => proteins.setQuery(e.target.value)}
          placeholder="Search proteins by name, gene, accession or organism…"
          className="h-14 w-full bg-transparent font-body text-base text-content-primary outline-none placeholder:text-content-muted"
        />
        {proteins.query && (
          <button
            type="button"
            onClick={() => proteins.setQuery("")}
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
            showFilters || proteins.activeFilterCount > 0
              ? "border-category-protein/50 text-category-protein"
              : "border-glass-border text-content-secondary hover:text-content-primary",
          )}
        >
          Filters{proteins.activeFilterCount > 0 ? ` · ${proteins.activeFilterCount}` : ""}
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
            <ProteinFilters
              filters={proteins.filters}
              onChange={proteins.setFilters}
              onReset={proteins.resetFilters}
            />
          </motion.div>
        )}
      </AnimatePresence>

      {/* View toggle */}
      <div className="flex items-center justify-end gap-2">
        <span className="eyebrow mr-1">View</span>
        <Button
          variant={view === "table" ? "category" : "ghost"}
          category="protein"
          size="sm"
          onClick={() => setView("table")}
        >
          Table
        </Button>
        <Button
          variant={view === "cards" ? "category" : "ghost"}
          category="protein"
          size="sm"
          onClick={() => setView("cards")}
        >
          Cards
        </Button>
      </div>

      {showCards ? (
        <div className="flex flex-col gap-4">
          <motion.div
            initial="hidden"
            animate="visible"
            className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3"
          >
            {proteins.results.map((protein) => (
              <ProteinCard key={protein.id} protein={protein} onView={openViewer} />
            ))}
          </motion.div>
          <div className="flex flex-col items-center justify-between gap-3 sm:flex-row">
            <span className="font-mono text-xs text-content-muted">Page {proteins.pageIndex + 1}</span>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={proteins.prevPage} disabled={!proteins.canPrev}>
                Previous
              </Button>
              <Button variant="outline" size="sm" onClick={proteins.nextPage} disabled={!proteins.canNext}>
                Next
              </Button>
            </div>
          </div>
        </div>
      ) : (
        <ProteinTable
          results={proteins.results}
          status={proteins.status}
          total={proteins.total}
          pageIndex={proteins.pageIndex}
          pageSize={proteins.pageSize}
          canPrev={proteins.canPrev}
          canNext={proteins.canNext}
          onPrev={proteins.prevPage}
          onNext={proteins.nextPage}
          onView={openViewer}
          onDownload={handleDownload}
        />
      )}

      <ProteinViewer protein={selected} open={viewerOpen} onClose={() => setViewerOpen(false)} />
    </div>
  );
}
