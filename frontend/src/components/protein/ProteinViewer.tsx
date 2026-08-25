"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import Link from "next/link";
import { AnimatePresence, motion } from "framer-motion";
import { viewerOverlayClass, viewerPanelClass, viewerPanelStyle } from "@/lib/viewer-overlay";
import { Badge, Button } from "@/components/ui";
import { CloseIcon, ExternalIcon } from "@/components/ui/Icons";
import { useCopyToClipboard } from "@/hooks/useCopyToClipboard";
import { getProtein } from "@/services/proteinService";
import { isApiConfigured } from "@/lib/api";
import {
  aaColor,
  AA_GROUP_COLOR,
  AA_GROUP_LABEL,
  downloadText,
  formatAa,
  formatMw,
  pdbUrl,
  toFasta,
  toJson,
  type AaGroup,
} from "@/lib/protein";
import type { ProteinSequence } from "@/types/protein";

const RENDER_CAP = 6000;
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
        <div key={rowIndex} className="flex min-w-0 gap-4">
          <span className="w-16 shrink-0 select-none text-right text-content-muted">
            {rowIndex * LINE_WIDTH + 1}
          </span>
          <span className="min-w-0 break-all tracking-[0.08em]">
            {line.split("").map((residue, i) => (
              <span key={i} style={{ color: aaColor(residue) }}>
                {residue}
              </span>
            ))}
          </span>
        </div>
      ))}
      {sequence.length > RENDER_CAP && (
        <p className="mt-4 text-xs text-content-muted">
          Showing first {new Intl.NumberFormat("en-US").format(RENDER_CAP)} of{" "}
          {new Intl.NumberFormat("en-US").format(sequence.length)} aa. Download the full
          record below.
        </p>
      )}
    </div>
  );
}

function GroupLegend() {
  return (
    <div className="flex flex-wrap items-center gap-3">
      {(Object.keys(AA_GROUP_COLOR) as AaGroup[]).map((group) => (
        <span key={group} className="flex items-center gap-1.5">
          <span className="h-2.5 w-2.5" style={{ backgroundColor: AA_GROUP_COLOR[group] }} />
          <span className="text-xs text-content-secondary">{AA_GROUP_LABEL[group]}</span>
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

export interface ProteinViewerProps {
  protein: ProteinSequence | null;
  open: boolean;
  onClose: () => void;
}

export function ProteinViewer({ protein, open, onClose }: ProteinViewerProps) {
  const [detail, setDetail] = useState<ProteinSequence | null>(protein);
  const [loading, setLoading] = useState(false);
  const [fullscreen, setFullscreen] = useState(false);
  const { copied, copy } = useCopyToClipboard();
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    setDetail(protein);
    setFullscreen(false);
  }, [protein]);

  useEffect(() => {
    if (!open || !protein || protein.sequence || !isApiConfigured) return;
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    setLoading(true);
    getProtein(protein.accession, controller.signal)
      .then((full) => {
        if (!controller.signal.aborted && full) setDetail(full);
      })
      .catch(() => undefined)
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [open, protein]);

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

  const active = detail ?? protein;
  const residues = active?.sequence ?? null;

  return createPortal(
    <AnimatePresence>
      {open && active && (
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
            <div className="flex shrink-0 items-start justify-between gap-4 border-b border-glass-divider p-6">
              <div className="flex min-w-0 flex-col gap-2">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge category="protein" dot>
                    Protein
                  </Badge>
                  {active.reviewed ? (
                    <Badge tone="success">Reviewed</Badge>
                  ) : (
                    <Badge tone="neutral">Unreviewed</Badge>
                  )}
                </div>
                <h2 className="truncate font-display text-xl font-bold tracking-tightest" title={active.name}>
                  {active.name}
                </h2>
                <span className="font-mono text-sm text-content-secondary">
                  {active.accession}
                  {active.gene ? ` · ${active.gene}` : ""} · {active.organism}
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

            <div className="flex min-h-0 flex-1 overflow-y-auto overscroll-contain">
            <div className="grid grid-cols-2 gap-3 border-b border-glass-divider p-6 sm:grid-cols-4">
              <MetaItem label="Length" value={formatAa(active.length)} />
              <MetaItem label="Molecular weight" value={formatMw(active.molecularWeight)} />
              <MetaItem label="Source" value={active.source} />
              <MetaItem label="Structures" value={active.pdbIds.length ? String(active.pdbIds.length) : "—"} />
            </div>

            {(active.function || active.domains.length > 0 || active.pdbIds.length > 0) && (
              <div className="flex flex-col gap-4 border-b border-glass-divider p-6">
                {active.function && (
                  <div className="flex flex-col gap-1.5">
                    <span className="eyebrow">Function</span>
                    <p className="text-sm leading-relaxed text-content-secondary">{active.function}</p>
                  </div>
                )}
                {active.domains.length > 0 && (
                  <div className="flex flex-col gap-2">
                    <span className="eyebrow">Domains</span>
                    <div className="flex flex-wrap gap-2">
                      {active.domains.map((domain) => (
                        <span
                          key={domain}
                          className="border border-glass-border px-2.5 py-1 font-mono text-xs text-content-secondary"
                        >
                          {domain}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                {active.pdbIds.length > 0 && (
                  <div className="flex flex-col gap-2">
                    <span className="eyebrow">3D structures · PDB</span>
                    <div className="flex flex-wrap gap-2">
                      {active.pdbIds.map((pdb) => (
                        <a
                          key={pdb}
                          href={pdbUrl(pdb)}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-1.5 border border-glass-border px-2.5 py-1 font-mono text-xs text-category-protein transition-colors hover:border-white/30"
                        >
                          {pdb}
                          <ExternalIcon className="h-3 w-3" />
                        </a>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            <div className="flex items-center justify-between gap-4 px-6 pt-5">
              <span className="eyebrow">Sequence · Residue view</span>
              <GroupLegend />
            </div>
            <div className="p-6">
              {loading ? (
                <p className="text-sm text-content-secondary">Loading residues from the database…</p>
              ) : residues ? (
                <SequenceView sequence={residues} />
              ) : (
                <p className="text-sm text-content-secondary">
                  Residues are served from the database. Connect the backend to view and
                  export the full sequence. Metadata above is preserved from the source.
                </p>
              )}
            </div>
            </div>

            <div className="flex shrink-0 flex-wrap items-center justify-end gap-3 border-t border-glass-divider p-6">
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
                onClick={() => downloadText(`${active.accession}.json`, toJson(active), "application/json")}
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
