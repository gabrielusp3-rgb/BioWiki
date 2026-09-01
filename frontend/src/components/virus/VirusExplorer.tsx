"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { cn } from "@/lib/cn";
import { Button } from "@/components/ui";
import { SearchIcon } from "@/components/ui/Icons";
import { VirusFilters } from "@/components/virus/VirusFilters";
import { VirusTable } from "@/components/virus/VirusTable";
import { VirusCard } from "@/components/virus/VirusCard";
import { VirusViewer } from "@/components/virus/VirusViewer";
import { useVirus } from "@/hooks/useVirus";
import { useQueryParamSync } from "@/hooks/useQueryParamSync";
import { getVirus } from "@/services/virusService";
import { downloadText, toFasta, toJson } from "@/lib/virus";
import type { VirusSequence } from "@/types/virus";

type ViewMode = "table" | "cards";

export function VirusExplorer() {
  const virus = useVirus();
  useQueryParamSync(virus.setQuery);
  const [showFilters, setShowFilters] = useState(false);
  const [view, setView] = useState<ViewMode>("table");
  const [selected, setSelected] = useState<VirusSequence | null>(null);
  const [viewerOpen, setViewerOpen] = useState(false);

  const openViewer = (seq: VirusSequence) => {
    setSelected(seq);
    setViewerOpen(true);
  };

  const handleDownload = async (seq: VirusSequence) => {
    let full: VirusSequence | null = seq;
    if (!seq.sequence) {
      try {
        full = (await getVirus(seq.accession)) ?? seq;
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

  const showCards = view === "cards" && virus.status === "success" && virus.results.length > 0;

  return (
    <div className="flex flex-col gap-6">
      <div
        className={cn(
          "glass hairline flex items-center gap-3 px-4 transition-colors duration-200",
          "focus-within:border-category-virus/50",
        )}
      >
        <SearchIcon className="h-5 w-5 shrink-0 text-content-secondary" />
        <input
          value={virus.query}
          onChange={(e) => virus.setQuery(e.target.value)}
          placeholder="Search viruses by name, family, accession or host…"
          className="h-14 w-full bg-transparent font-body text-base text-content-primary outline-none placeholder:text-content-muted"
        />
        {virus.query && (
          <button
            type="button"
            onClick={() => virus.setQuery("")}
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
            showFilters || virus.activeFilterCount > 0
              ? "border-category-virus/50 text-category-virus"
              : "border-glass-border text-content-secondary hover:text-content-primary",
          )}
        >
          Filters{virus.activeFilterCount > 0 ? ` · ${virus.activeFilterCount}` : ""}
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
            <VirusFilters filters={virus.filters} onChange={virus.setFilters} onReset={virus.resetFilters} />
          </motion.div>
        )}
      </AnimatePresence>

      <div className="flex items-center justify-end gap-2">
        <span className="eyebrow mr-1">View</span>
        <Button
          variant={view === "table" ? "category" : "ghost"}
          category="virus"
          size="sm"
          onClick={() => setView("table")}
        >
          Table
        </Button>
        <Button
          variant={view === "cards" ? "category" : "ghost"}
          category="virus"
          size="sm"
          onClick={() => setView("cards")}
        >
          Cards
        </Button>
      </div>

      {showCards ? (
        <div className="flex flex-col gap-4">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {virus.results.map((item) => (
              <VirusCard key={item.id} virus={item} onView={openViewer} />
            ))}
          </div>
          <div className="flex flex-col items-center justify-between gap-3 sm:flex-row">
            <span className="font-mono text-xs text-content-muted">Page {virus.pageIndex + 1}</span>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={virus.prevPage} disabled={!virus.canPrev}>
                Previous
              </Button>
              <Button variant="outline" size="sm" onClick={virus.nextPage} disabled={!virus.canNext}>
                Next
              </Button>
            </div>
          </div>
        </div>
      ) : (
        <VirusTable
          results={virus.results}
          status={virus.status}
          total={virus.total}
          pageIndex={virus.pageIndex}
          pageSize={virus.pageSize}
          canPrev={virus.canPrev}
          canNext={virus.canNext}
          onPrev={virus.prevPage}
          onNext={virus.nextPage}
          onView={openViewer}
          onDownload={handleDownload}
        />
      )}

      <VirusViewer virus={selected} open={viewerOpen} onClose={() => setViewerOpen(false)} />
    </div>
  );
}
