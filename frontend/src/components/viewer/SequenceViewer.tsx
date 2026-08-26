"use client";

import { useEffect, useMemo, useState } from "react";
import { createPortal } from "react-dom";
import Link from "next/link";
import { AnimatePresence, motion } from "framer-motion";
import {
  viewerBodyClass,
  viewerOverlayClass,
  viewerPanelClass,
  viewerPanelStyle,
} from "@/lib/viewer-overlay";
import { Badge } from "@/components/ui";
import { CloseIcon } from "@/components/ui/Icons";
import { useCopyToClipboard } from "@/hooks/useCopyToClipboard";
import type { CategoryKey } from "@/lib/design-tokens";
import {
  buildFasta,
  downloadText,
  legendFor,
  type Molecule,
  type SequenceKind,
} from "@/lib/sequence-colors";
import { SequenceHighlight } from "@/components/viewer/SequenceHighlight";
import { SequenceToolbar } from "@/components/viewer/SequenceToolbar";

export interface SequenceMetaItem {
  label: string;
  value: string;
}

export interface SequenceViewerProps {
  /** FASTA header/description line (without the leading ">"). */
  header: string;
  /** Short title shown in the panel head. */
  title: string;
  /** Accession or identifier shown as a subtitle. */
  subtitle?: string;
  /** Raw residues — null while awaiting the database; never fabricated. */
  sequence: string | null;
  kind: SequenceKind;
  /** For nucleotides, controls the T (DNA) vs U (RNA) legend. */
  molecule?: Molecule;
  /** Accent colour, defaults per kind. */
  accent?: CategoryKey;
  /** Base filename for downloads (without extension). */
  filename: string;
  /** Optional JSON payload for the JSON download; omit to hide the button. */
  jsonPayload?: unknown;
  /** Optional metadata grid rendered above the sequence. */
  meta?: SequenceMetaItem[];
  /** Loading state while residues are fetched. */
  loading?: boolean;
  /** Message shown when there are no residues to display. */
  emptyMessage?: string;
  lineWidth?: number;
  renderCap?: number;
  showLineNumbers?: boolean;
  /** Route of the full record page (e.g. `/sequences/NM_000546`). */
  detailHref?: string;

  /** Modal mode. When `asModal` is true the viewer renders in a portal overlay. */
  asModal?: boolean;
  open?: boolean;
  onClose?: () => void;
}

const DEFAULT_ACCENT: Record<SequenceKind, CategoryKey> = {
  nucleotide: "dna",
  protein: "protein",
};

const DEFAULT_EMPTY =
  "Residues are served from the database. Connect the backend to view and export the full record.";

function MetaGrid({ meta }: { meta: SequenceMetaItem[] }) {
  return (
    <div className="grid grid-cols-2 gap-3 border-b border-glass-divider p-6 sm:grid-cols-4">
      {meta.map((item) => (
        <div key={item.label} className="flex flex-col gap-1 border border-glass-divider p-3">
          <span className="eyebrow">{item.label}</span>
          <span className="truncate font-mono text-sm text-content-primary" title={item.value}>
            {item.value}
          </span>
        </div>
      ))}
    </div>
  );
}

/**
 * Inner content shared by inline and modal renderings: head, toolbar, metadata
 * and the highlighted sequence body.
 */
function ViewerBody(props: {
  data: SequenceViewerProps;
  fullscreen: boolean;
  onToggleFullscreen?: () => void;
  onClose?: () => void;
}) {
  const { data, fullscreen, onToggleFullscreen, onClose } = props;
  const {
    header,
    title,
    subtitle,
    sequence,
    kind,
    molecule = "dna",
    accent,
    filename,
    jsonPayload,
    meta,
    loading,
    emptyMessage = DEFAULT_EMPTY,
    lineWidth = 60,
    renderCap,
    showLineNumbers = true,
  } = data;

  const { copied, copy } = useCopyToClipboard();
  const resolvedAccent = accent ?? DEFAULT_ACCENT[kind];
  const legend = useMemo(() => legendFor(kind, molecule), [kind, molecule]);
  const canExport = Boolean(sequence);

  const handleCopy = () => {
    if (sequence) copy(buildFasta(header, sequence, lineWidth));
  };
  const handleFasta = () => {
    if (sequence) downloadText(`${filename}.fasta`, buildFasta(header, sequence, lineWidth));
  };
  const handleJson =
    jsonPayload !== undefined
      ? () =>
          downloadText(
            `${filename}.json`,
            JSON.stringify(jsonPayload, null, 2),
            "application/json",
          )
      : undefined;

  return (
    <>
      <div className="flex shrink-0 items-start justify-between gap-4 border-b border-glass-divider p-6">
        <div className="flex min-w-0 flex-col gap-2">
          <Badge category={resolvedAccent} dot>
            {kind === "protein" ? "Protein" : molecule === "rna" ? "RNA" : "DNA"}
          </Badge>
          <h2 className="truncate font-display text-xl font-bold tracking-tightest" title={title}>
            {title}
          </h2>
          {subtitle && (
            <span className="font-mono text-sm text-content-secondary">{subtitle}</span>
          )}
          {data.detailHref && (
            <Link
              href={data.detailHref}
              onClick={onClose}
              className="mt-1 w-fit border border-glass-border px-3 py-1.5 font-display text-[11px] font-semibold uppercase tracking-wide text-content-secondary transition-colors hover:border-white/30 hover:text-content-primary"
            >
              Full record →
            </Link>
          )}
        </div>
        {onClose && (
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="grid h-9 w-9 shrink-0 place-items-center border border-glass-border text-content-secondary transition-colors hover:border-white/30 hover:text-content-primary"
          >
            <CloseIcon className="h-5 w-5" />
          </button>
        )}
      </div>

      <div className={viewerBodyClass}>
      {meta && meta.length > 0 && <MetaGrid meta={meta} />}
      <SequenceToolbar
        legend={legend}
        copied={copied}
        canExport={canExport}
        onCopy={handleCopy}
        onDownloadFasta={handleFasta}
        onDownloadJson={handleJson}
        fullscreen={fullscreen}
        onToggleFullscreen={onToggleFullscreen}
      />

      <div className="p-6">
        {loading ? (
          <p className="text-sm text-content-secondary">Loading residues from the database…</p>
        ) : sequence ? (
          <SequenceHighlight
            sequence={sequence}
            kind={kind}
            molecule={molecule}
            lineWidth={lineWidth}
            renderCap={renderCap}
            showLineNumbers={showLineNumbers}
          />
        ) : (
          <p className="text-sm text-content-secondary">{emptyMessage}</p>
        )}
      </div>
      </div>
    </>
  );
}

/**
 * SequenceViewer — reusable FASTA viewer with syntax highlighting, line
 * numbers, copy, download and fullscreen. Works inline or as a modal.
 *
 * Colouring: A → cyan, T → magenta, G → green, C → yellow (U mirrors T for
 * RNA); proteins use a physicochemical amino-acid palette.
 */
export function SequenceViewer(props: SequenceViewerProps) {
  const { asModal, open, onClose } = props;
  const [fullscreen, setFullscreen] = useState(false);

  useEffect(() => {
    if (!asModal || !open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose?.();
    window.addEventListener("keydown", onKey);
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      window.removeEventListener("keydown", onKey);
      document.body.style.overflow = prev;
    };
  }, [asModal, open, onClose]);

  useEffect(() => {
    if (!open) setFullscreen(false);
  }, [open]);

  if (!asModal) {
    return (
      <div className="glass-strong flex max-h-[80dvh] min-h-0 flex-col overflow-hidden">
        <ViewerBody data={props} fullscreen={false} />
      </div>
    );
  }

  if (typeof document === "undefined") return null;

  return createPortal(
    <AnimatePresence>
      {open && (
        <div className={viewerOverlayClass(fullscreen)}>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.18 }}
            onClick={onClose}
            className="absolute inset-0 bg-black/80 backdrop-blur-sm"
          />
          <motion.div
            initial={{ opacity: 0, y: 24, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 16, scale: 0.98 }}
            transition={{ duration: 0.28, ease: [0.22, 1, 0.36, 1] }}
            className={viewerPanelClass({ fullscreen })}
            style={viewerPanelStyle(fullscreen)}
          >
            <ViewerBody
              data={props}
              fullscreen={fullscreen}
              onToggleFullscreen={() => setFullscreen((v) => !v)}
              onClose={onClose}
            />
          </motion.div>
        </div>
      )}
    </AnimatePresence>,
    document.body,
  );
}
