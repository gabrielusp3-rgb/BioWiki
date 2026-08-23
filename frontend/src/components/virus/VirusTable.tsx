"use client";

import { Badge, Button, Skeleton, Table, type Column } from "@/components/ui";
import { DownloadIcon } from "@/components/ui/Icons";
import { formatBases } from "@/lib/virus";
import type { VirusStatus } from "@/hooks/useVirus";
import type { VirusSequence } from "@/types/virus";

interface VirusTableProps {
  results: VirusSequence[];
  status: VirusStatus;
  total: number;
  pageIndex: number;
  pageSize: number;
  canPrev: boolean;
  canNext: boolean;
  onPrev: () => void;
  onNext: () => void;
  onView: (seq: VirusSequence) => void;
  onDownload: (seq: VirusSequence) => void;
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

export function VirusTable({
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
}: VirusTableProps) {
  const columns: Column<VirusSequence>[] = [
    {
      key: "accession",
      header: "Accession",
      render: (row) => (
        <button
          type="button"
          onClick={() => onView(row)}
          className="font-mono text-xs text-category-virus hover:underline"
        >
          {row.accession}
          {row.version ? `.${row.version}` : ""}
        </button>
      ),
    },
    {
      key: "name",
      header: "Virus",
      render: (row) => (
        <span className="block max-w-[260px] truncate text-content-primary" title={row.name}>
          {row.name}
        </span>
      ),
    },
    {
      key: "family",
      header: "Family",
      render: (row) => <span className="text-xs text-content-secondary">{row.family}</span>,
    },
    {
      key: "host",
      header: "Host",
      render: (row) => <span className="italic text-content-secondary">{row.host ?? "—"}</span>,
    },
    {
      key: "genome",
      header: "Genome",
      render: (row) => <Badge category="virus">{row.genomeType}</Badge>,
    },
    {
      key: "length",
      header: "Length",
      align: "right",
      render: (row) => <span className="font-mono text-xs">{formatBases(row)}</span>,
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
        detail="Live viral records appear once the sequence database is connected. No sample or placeholder data is shown."
      />
    );
  }

  if (status === "error") {
    return (
      <StateMessage
        title="Unable to load viruses"
        detail="The service is temporarily unavailable. Please try again shortly."
      />
    );
  }

  if (status === "success" && results.length === 0) {
    return (
      <StateMessage
        title="No viruses found"
        detail="No viral records match the current search and filters."
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
