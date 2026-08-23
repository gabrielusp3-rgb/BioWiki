"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import Link from "next/link";
import { AnimatePresence, motion } from "framer-motion";
import { cn } from "@/lib/cn";
import { Badge, Button } from "@/components/ui";
import { CloseIcon } from "@/components/ui/Icons";
import { useCopyToClipboard } from "@/hooks/useCopyToClipboard";
import { getRna } from "@/services/rnaService";
import { isApiConfigured } from "@/lib/api";
import {
  baseColor,
  downloadText,
  formatGc,
  formatNt,
  RNA_CLASS_LABEL,
  toFasta,
  toJson,
} from "@/lib/rna";
import { baseColors } from "@/lib/design-tokens";
import type { RnaSequence } from "@/types/rna";

const RENDER_CAP = 9000;
const LINE_WIDTH = 60;

function SequenceView({ sequence }: { sequence: string }) {
  const lines = useMemo(() => {
    const capped = sequence.slice(0, RENDER_CAP);
    const rows: string[] = [];
    for (let i = 0; i < capped.length; i += LINE_WIDTH) {
      rows.push(capped.slice(i, i + LINE_WIDTH));
    }
    return rows;
  }, [sequence]);

  return (
    <div className="font-mono text-[13px] leading-6">
      {lines.map((line, rowIndex) => (
        <div key={rowIndex} className="flex gap-4">
          <span className="w-16 shrink-0 select-none text-right text-content-muted">
            {rowIndex * LINE_WIDTH + 1}
          </span>
          <span className="tracking-[0.15em]">
            {line.split("").map((base, i) => (
              <span key={i} style={{ color: baseColor(base) }}>
                {base}
              </span>
            ))}
          </span>
        </div>
      ))}
      {sequence.length > RENDER_CAP && (
        <p className="mt-4 text-xs text-content-muted">
          Showing first {new Intl.NumberFormat("en-US").format(RENDER_CAP)} of{" "}
          {new Intl.NumberFormat("en-US").format(sequence.length)} nt. Download the full
          record below.
        </p>
      )}
    </div>
  );
}

function BaseLegend() {
  return (
    <div className="flex flex-wrap items-center gap-3">
      {(["A", "U", "G", "C"] as const).map((base) => (
        <span key={base} className="flex items-center gap-1.5">
          <span className="h-2.5 w-2.5" style={{ backgroundColor: baseColors[base] }} />
          <span className="font-mono text-xs text-content-secondary">{base}</span>
        </span>
      ))}
    </div>
  );
}

function MetaItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-1 border border-glass-divider p-3">
      <span className="eyebrow">{label}</span>
      <span className="truncate font-mono text-sm text-content-primary" title={value}>
        {value}
      </span>
    </div>
  );
}

export interface RNAViewerProps {
  sequence: RnaSequence | null;
  open: boolean;
  onClose: () => void;
}

export function RNAViewer({ sequence, open, onClose }: RNAViewerProps) {
  const [detail, setDetail] = useState<RnaSequence | null>(sequence);
  const [loading, setLoading] = useState(false);
  const [fullscreen, setFullscreen] = useState(false);
  const { copied, copy } = useCopyToClipboard();
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    setDetail(sequence);
    setFullscreen(false);
  }, [sequence]);

  useEffect(() => {
    if (!open || !sequence || sequence.sequence || !isApiConfigured) return;
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    setLoading(true);
    getRna(sequence.accession, controller.signal)
      .then((full) => {
        if (!controller.signal.aborted && full) setDetail(full);
      })
      .catch(() => undefined)
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [open, sequence]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      window.removeEventListener("keydown", onKey);
      document.body.style.overflow = prev;
    };
  }, [open, onClose]);

  if (typeof document === "undefined") return null;

  const active = detail ?? sequence;
  const residues = active?.sequence ?? null;

  return createPortal(
    <AnimatePresence>
      {open && active && (
        <div className="fixed inset-0 z-[1000] grid place-items-center p-0 sm:p-6">
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
            className={cn(
              "glass-strong relative z-10 flex w-full flex-col",
              fullscreen ? "h-full max-w-none sm:h-full" : "max-h-[90dvh] max-w-4xl",
            )}
          >
            <div className="flex items-start justify-between gap-4 border-b border-glass-divider p-6">
              <div className="flex min-w-0 flex-col gap-2">
                <div className="flex items-center gap-2">
                  <Badge category="rna" dot>
                    RNA
                  </Badge>
                  <Badge category="rna">{RNA_CLASS_LABEL[active.rnaClass]}</Badge>
                </div>
                <h2 className="truncate font-display text-xl font-bold tracking-tightest" title={active.name}>
                  {active.name}
                </h2>
                <span className="font-mono text-sm text-content-secondary">
                  {active.accession}
                  {active.version ? `.${active.version}` : ""} · {active.organism}
                </span>
                <Link
                  href={`/sequences/${encodeURIComponent(active.accession)}`}
                  onClick={onClose}
                  className="mt-1 w-fit border border-glass-border px-3 py-1.5 font-display text-[11px] font-semibold uppercase tracking-wide text-content-secondary transition-colors hover:border-white/30 hover:text-content-primary"
                >
                  Full record →
                </Link>
              </div>
              <div className="flex shrink-0 items-center gap-2">
                <button
                  type="button"
                  onClick={() => setFullscreen((v) => !v)}
                  aria-label="Toggle fullscreen"
                  className="hidden h-9 w-9 place-items-center border border-glass-border text-content-secondary transition-colors hover:border-white/30 hover:text-content-primary sm:grid"
                >
                  <span className="text-xs">{fullscreen ? "▢" : "⤢"}</span>
                </button>
                <button
                  type="button"
                  onClick={onClose}
                  aria-label="Close"
                  className="grid h-9 w-9 place-items-center border border-glass-border text-content-secondary transition-colors hover:border-white/30 hover:text-content-primary"
                >
                  <CloseIcon className="h-5 w-5" />
                </button>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3 border-b border-glass-divider p-6 sm:grid-cols-4">
              <MetaItem label="Length" value={formatNt(active.length)} />
              <MetaItem label="GC content" value={formatGc(active.gcContent)} />
              <MetaItem label="Coding" value={active.isCoding ? "Coding" : "Non-coding"} />
              <MetaItem label="Source" value={active.source} />
            </div>

            <div className="flex items-center justify-between gap-4 px-6 pt-5">
              <span className="eyebrow">FASTA · Base view</span>
              <BaseLegend />
            </div>
            <div className="min-h-[160px] flex-1 overflow-auto p-6">
              {loading ? (
                <p className="text-sm text-content-secondary">Loading residues from the database…</p>
              ) : residues ? (
                <SequenceView sequence={residues} />
              ) : (
                <p className="text-sm text-content-secondary">
                  Residues are served from the database. Connect the backend to view and
                  export the full FASTA record. Metadata above is preserved from the source.
                </p>
              )}
            </div>

            <div className="flex flex-wrap items-center justify-end gap-3 border-t border-glass-divider p-6">
              <Button
                variant="ghost"
                size="sm"
                disabled={!residues}
                onClick={() => residues && copy(toFasta(active))}
              >
                {copied ? "Copied" : "Copy FASTA"}
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={!residues}
                onClick={() => downloadText(`${active.accession}.fasta`, toFasta(active), "text/plain")}
              >
                Download FASTA
              </Button>
              <Button
                variant="glass"
                size="sm"
                onClick={() =>
                  downloadText(`${active.accession}.json`, toJson(active), "application/json")
                }
              >
                Download JSON
              </Button>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>,
    document.body,
  );
}
