"use client";

import { Badge, Button, Skeleton, Table, type Column } from "@/components/ui";
import { DownloadIcon } from "@/components/ui/Icons";
import { CAS_SYSTEM_LABEL, CRISPR_EVIDENCE_LABEL, formatNt, formatScore } from "@/lib/crispr";
import type { CrisprStatus } from "@/hooks/useCrispr";
import type { CrisprGuide } from "@/types/crispr";

interface CRISPRTableProps {
  results: CrisprGuide[];
  status: CrisprStatus;
  total: number;
  pageIndex: number;
  pageSize: number;
  canPrev: boolean;
  canNext: boolean;
  onPrev: () => void;
  onNext: () => void;
  onView: (guide: CrisprGuide) => void;
  onDownload: (guide: CrisprGuide) => void;
}

function StateMessage({ title, detail }: { title: string; detail: string }) {
  return (
    <div className="glass flex flex-col items-center gap-2 px-6 py-16 text-center">
      <span className="font-display text-sm font-bold uppercase tracking-wide text-content-primary">
        {title}
      </span>
      <span className="max-w-md text-sm text-content-secondary">{detail}</span>
    </div>
  );
}

export function CRISPRTable({
  results,
  status,
  total,
  pageIndex,
  pageSize,
  canPrev,
  canNext,
  onPrev,
  onNext,
  onView,
  onDownload,
}: CRISPRTableProps) {
  const columns: Column<CrisprGuide>[] = [
    {
      key: "accession",
      header: "Guide ID",
      render: (row) => (
        <button
          type="button"
          onClick={() => onView(row)}
          className="font-mono text-xs text-category-crispr hover:underline"
        >
          {row.accession}
        </button>
      ),
    },
    {
      key: "target",
      header: "Target gene",
      render: (row) => <span className="font-mono text-xs text-content-primary">{row.targetGene}</span>,
    },
    {
      key: "organism",
      header: "Organism",
      render: (row) => <span className="italic text-content-secondary">{row.organism}</span>,
    },
    {
      key: "system",
      header: "System",
      render: (row) => <Badge category="crispr">{CAS_SYSTEM_LABEL[row.system]}</Badge>,
    },
    {
      key: "evidence",
      header: "Evidence",
      render: (row) => (
        <span className="text-xs text-content-secondary">
          {CRISPR_EVIDENCE_LABEL[row.evidenceType ?? "natural_crispr_element"]}
        </span>
      ),
    },
    {
      key: "pam",
      header: "PAM",
      render: (row) => <span className="font-mono text-xs text-content-secondary">{row.pam}</span>,
    },
    {
      key: "length",
      header: "Length",
      align: "right",
      render: (row) => <span className="font-mono text-xs">{formatNt(row.guideLength)}</span>,
    },
    {
      key: "onTarget",
      header: "On-target",
      align: "right",
      render: (row) => (
        <span className="font-mono text-xs text-content-secondary">{formatScore(row.onTargetScore)}</span>
      ),
    },
    {
      key: "offTarget",
      header: "Off-target",
      align: "right",
      render: (row) => (
        <span className="font-mono text-xs text-content-secondary">{formatScore(row.offTargetScore)}</span>
      ),
    },
    {
      key: "actions",
      header: "",
      align: "right",
      render: (row) => (
        <div className="flex items-center justify-end gap-2">
          <Button variant="ghost" size="sm" onClick={() => onView(row)}>
            View
          </Button>
          <button
            type="button"
            onClick={() => onDownload(row)}
            aria-label={`Download ${row.accession}`}
            className="grid h-9 w-9 place-items-center border border-glass-border text-content-secondary transition-colors hover:border-white/30 hover:text-content-primary"
          >
            <DownloadIcon className="h-4 w-4" />
          </button>
        </div>
      ),
    },
  ];

  if (status === "loading") {
    return (
      <div className="flex flex-col gap-2">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} height={56} />
        ))}
      </div>
    );
  }

  if (status === "unavailable") {
    return (
      <StateMessage
        title="Database not connected"
        detail="Live CRISPR guides appear once the sequence database is connected. No sample or placeholder data is shown."
      />
    );
  }

  if (status === "error") {
    return (
      <StateMessage
        title="Unable to load guides"
        detail="The service is temporarily unavailable. Please try again shortly."
      />
    );
  }

  if (status === "success" && results.length === 0) {
    return (
      <StateMessage
        title="No guides found"
        detail="No CRISPR guides match the current search and filters."
      />
    );
  }

  const from = pageIndex * pageSize + 1;
  const to = pageIndex * pageSize + results.length;

  return (
    <div className="flex flex-col gap-4">
      <Table columns={columns} data={results} rowKey={(row) => row.id} />

      <div className="flex flex-col items-center justify-between gap-3 sm:flex-row">
        <span className="font-mono text-xs text-content-muted">
          Showing {from}–{to}
          {total > 0 ? ` of ${new Intl.NumberFormat("en-US").format(total)}` : ""}
        </span>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={onPrev} disabled={!canPrev}>
            Previous
          </Button>
          <span className="px-2 font-mono text-xs text-content-secondary">Page {pageIndex + 1}</span>
          <Button variant="outline" size="sm" onClick={onNext} disabled={!canNext}>
            Next
          </Button>
        </div>
      </div>
    </div>
  );
}
