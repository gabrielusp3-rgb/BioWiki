"use client";

import { Badge, Button, Skeleton, Table, type Column } from "@/components/ui";
import { DownloadIcon } from "@/components/ui/Icons";
import { formatGc, formatNt, RNA_CLASS_LABEL } from "@/lib/rna";
import type { RnaStatus } from "@/hooks/useRnaSequences";
import type { RnaSequence } from "@/types/rna";

interface RNATableProps {
  results: RnaSequence[];
  status: RnaStatus;
  total: number;
  pageIndex: number;
  pageSize: number;
  canPrev: boolean;
  canNext: boolean;
  onPrev: () => void;
  onNext: () => void;
  onView: (seq: RnaSequence) => void;
  onDownload: (seq: RnaSequence) => void;
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

export function RNATable({
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
}: RNATableProps) {
  const columns: Column<RnaSequence>[] = [
    {
      key: "accession",
      header: "Accession",
      render: (row) => (
        <button
          type="button"
          onClick={() => onView(row)}
          className="font-mono text-xs text-category-rna hover:underline"
        >
          {row.accession}
          {row.version ? `.${row.version}` : ""}
        </button>
      ),
    },
    {
      key: "name",
      header: "Definition",
      render: (row) => (
        <span className="block max-w-[280px] truncate text-content-primary" title={row.name}>
          {row.name}
        </span>
      ),
    },
    {
      key: "organism",
      header: "Organism",
      render: (row) => <span className="italic text-content-secondary">{row.organism}</span>,
    },
    {
      key: "class",
      header: "Class",
      render: (row) => <Badge category="rna">{RNA_CLASS_LABEL[row.rnaClass]}</Badge>,
    },
    {
      key: "coding",
      header: "Coding",
      render: (row) => (
        <span className="text-xs text-content-secondary">{row.isCoding ? "Coding" : "Non-coding"}</span>
      ),
    },
    {
      key: "length",
      header: "Length",
      align: "right",
      render: (row) => <span className="font-mono text-xs">{formatNt(row.length)}</span>,
    },
    {
      key: "gc",
      header: "GC",
      align: "right",
      render: (row) => (
        <span className="font-mono text-xs text-content-secondary">{formatGc(row.gcContent)}</span>
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
        detail="Live RNA records appear once the sequence database is connected. No sample or placeholder data is shown."
      />
    );
  }

  if (status === "error") {
    return (
      <StateMessage
        title="Unable to load sequences"
        detail="The service is temporarily unavailable. Please try again shortly."
      />
    );
  }

  if (status === "success" && results.length === 0) {
    return (
      <StateMessage
        title="No sequences found"
        detail="No RNA records match the current search and filters."
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
