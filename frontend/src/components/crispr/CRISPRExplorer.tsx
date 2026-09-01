"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { cn } from "@/lib/cn";
import { CRISPRFilters } from "@/components/crispr/CRISPRFilters";
import { CRISPRTable } from "@/components/crispr/CRISPRTable";
import { CRISPRViewer } from "@/components/crispr/CRISPRViewer";
import { CatalogueTotalLine } from "@/components/stats/CatalogueTotalLine";
import { SearchIcon } from "@/components/ui/Icons";
import { useCrispr } from "@/hooks/useCrispr";
import { useQueryParamSync } from "@/hooks/useQueryParamSync";
import { getCrispr } from "@/services/crisprService";
import { downloadText, toFasta, toJson } from "@/lib/crispr";
import type { CrisprGuide } from "@/types/crispr";

export function CRISPRExplorer() {
  const crispr = useCrispr();
  useQueryParamSync(crispr.setQuery);
  const [showFilters, setShowFilters] = useState(false);
  const [selected, setSelected] = useState<CrisprGuide | null>(null);
  const [viewerOpen, setViewerOpen] = useState(false);

  const openViewer = (guide: CrisprGuide) => {
    setSelected(guide);
    setViewerOpen(true);
  };

  const handleDownload = async (guide: CrisprGuide) => {
    let full: CrisprGuide | null = guide;
    if (!guide.guideSequence) {
      try {
        full = (await getCrispr(guide.accession)) ?? guide;
      } catch {
        full = guide;
      }
    }
    if (full.guideSequence) {
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
          "focus-within:border-category-crispr/50",
        )}
      >
        <SearchIcon className="h-5 w-5 shrink-0 text-content-secondary" />
        <input
          value={crispr.query}
          onChange={(e) => crispr.setQuery(e.target.value)}
          placeholder="Search guides by target gene, ID, PAM or organism…"
          className="h-14 w-full bg-transparent font-body text-base text-content-primary outline-none placeholder:text-content-muted"
        />
        {crispr.query && (
          <button
            type="button"
            onClick={() => crispr.setQuery("")}
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
            showFilters || crispr.activeFilterCount > 0
              ? "border-category-crispr/50 text-category-crispr"
              : "border-glass-border text-content-secondary hover:text-content-primary",
          )}
        >
          Filters{crispr.activeFilterCount > 0 ? ` · ${crispr.activeFilterCount}` : ""}
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
            <CRISPRFilters
              filters={crispr.filters}
              onChange={crispr.setFilters}
              onReset={crispr.resetFilters}
            />
          </motion.div>
        )}
      </AnimatePresence>

      <CatalogueTotalLine status={crispr.status} total={crispr.total} noun="CRISPR records" />

      <CRISPRTable
        results={crispr.results}
        status={crispr.status}
        total={crispr.total}
        pageIndex={crispr.pageIndex}
        pageSize={crispr.pageSize}
        canPrev={crispr.canPrev}
        canNext={crispr.canNext}
        onPrev={crispr.prevPage}
        onNext={crispr.nextPage}
        onView={openViewer}
        onDownload={handleDownload}
      />

      <CRISPRViewer guide={selected} open={viewerOpen} onClose={() => setViewerOpen(false)} />
    </div>
  );
}
