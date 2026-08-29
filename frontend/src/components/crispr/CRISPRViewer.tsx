"use client";

import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import Link from "next/link";
import { AnimatePresence, motion } from "framer-motion";
import {
  viewerBodyClass,
  viewerOverlayClass,
  viewerPanelClass,
  viewerPanelStyle,
} from "@/lib/viewer-overlay";
import { Badge, Button } from "@/components/ui";
import { CloseIcon } from "@/components/ui/Icons";
import { useCopyToClipboard } from "@/hooks/useCopyToClipboard";
import { getCrispr } from "@/services/crisprService";
import { isApiConfigured } from "@/lib/api";
import {
  baseColor,
  CAS_SYSTEM_LABEL,
  CRISPR_EVIDENCE_LABEL,
  downloadText,
  formatNt,
  formatScore,
  toFasta,
  toJson,
} from "@/lib/crispr";
import { baseColors } from "@/lib/design-tokens";
import type { CrisprGuide } from "@/types/crispr";

function GuideRuler({ sequence, pam }: { sequence: string; pam: string }) {
  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center gap-1 font-mono text-lg tracking-[0.25em]">
        {sequence.split("").map((base, i) => (
          <span key={i} style={{ color: baseColor(base) }}>
            {base}
          </span>
        ))}
        {pam && (
          <span className="ml-2 flex items-center gap-1">
            <span className="border border-category-crispr/50 bg-category-crispr/10 px-2 py-0.5 text-sm text-category-crispr">
              {pam}
            </span>
            <span className="text-[10px] uppercase tracking-wider text-content-muted">PAM</span>
          </span>
        )}
      </div>
      <div className="flex flex-wrap items-center gap-3">
        {(["A", "T", "G", "C"] as const).map((base) => (
          <span key={base} className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5" style={{ backgroundColor: baseColors[base] }} />
            <span className="font-mono text-xs text-content-secondary">{base}</span>
          </span>
        ))}
      </div>
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

export interface CRISPRViewerProps {
  guide: CrisprGuide | null;
  open: boolean;
  onClose: () => void;
}

export function CRISPRViewer({ guide, open, onClose }: CRISPRViewerProps) {
  const [detail, setDetail] = useState<CrisprGuide | null>(guide);
  const [loading, setLoading] = useState(false);
  const { copied, copy } = useCopyToClipboard();
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => setDetail(guide), [guide]);

  useEffect(() => {
    if (!open || !guide || guide.guideSequence || !isApiConfigured) return;
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    setLoading(true);
    getCrispr(guide.accession, controller.signal)
      .then((full) => {
        if (!controller.signal.aborted && full) setDetail(full);
      })
      .catch(() => undefined)
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [open, guide]);

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

  const active = detail ?? guide;
  const residues = active?.guideSequence ?? null;

  return createPortal(
    <AnimatePresence>
      {open && active && (
        <div className={viewerOverlayClass()}>
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
            className={viewerPanelClass({ maxWidth: "max-w-3xl" })}
            style={viewerPanelStyle()}
          >
            <div className="flex shrink-0 items-start justify-between gap-4 border-b border-glass-divider p-6">
              <div className="flex min-w-0 flex-col gap-2">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge category="crispr" dot>
                    CRISPR
                  </Badge>
                  <Badge category="crispr">{CAS_SYSTEM_LABEL[active.system]}</Badge>
                  <Badge category="crispr">
                    {CRISPR_EVIDENCE_LABEL[active.evidenceType ?? "natural_crispr_element"]}
                  </Badge>
                </div>
                <h2 className="truncate font-display text-xl font-bold tracking-tightest" title={active.name}>
                  {active.name}
                </h2>
                <span className="font-mono text-sm text-content-secondary">
                  {active.accession} · target {active.targetGene} · {active.organism}
                </span>
                <Link
                  href={`/sequences/${encodeURIComponent(active.accession)}`}
                  onClick={onClose}
                  className="mt-1 w-fit border border-glass-border px-3 py-1.5 font-display text-[11px] font-semibold uppercase tracking-wide text-content-secondary transition-colors hover:border-white/30 hover:text-content-primary"
                >
                  Full record →
                </Link>
              </div>
              <button
                type="button"
                onClick={onClose}
                aria-label="Close"
                className="grid h-9 w-9 shrink-0 place-items-center border border-glass-border text-content-secondary transition-colors hover:border-white/30 hover:text-content-primary"
              >
                <CloseIcon className="h-5 w-5" />
              </button>
            </div>

            <div className={viewerBodyClass}>
            <div className="grid grid-cols-2 gap-3 border-b border-glass-divider p-6 sm:grid-cols-4">
              <MetaItem label="PAM" value={active.pam} />
              <MetaItem label="Length" value={formatNt(active.guideLength)} />
              <MetaItem label="On-target" value={formatScore(active.onTargetScore)} />
              <MetaItem label="Off-target" value={formatScore(active.offTargetScore)} />
            </div>

            <div className="flex flex-col gap-4 p-6">
              <span className="eyebrow">
                {active.evidenceType === "computational_target"
                  ? "Predicted spacer (computational)"
                  : active.evidenceType === "experimental_guide"
                    ? "Experimental guide"
                    : "CRISPR sequence"}
              </span>
              {loading ? (
                <p className="text-sm text-content-secondary">Loading guide from the database…</p>
              ) : residues ? (
                <GuideRuler sequence={residues} pam={active.pam} />
              ) : (
                <p className="text-sm text-content-secondary">
                  The guide/spacer sequence is served from the database. Connect the backend
                  to view and export it. Metadata above is preserved from the source.
                </p>
              )}

              {active.genomicTarget && (
                <div className="flex flex-col gap-1.5 border-t border-glass-divider pt-4">
                  <span className="eyebrow">Genomic target</span>
                  <span className="font-mono text-sm text-content-primary">{active.genomicTarget}</span>
                </div>
              )}

              {active.targetSourceAccession && (
                <div className="flex flex-col gap-1.5 border-t border-glass-divider pt-4">
                  <span className="eyebrow">Target accession</span>
                  <span className="font-mono text-sm text-content-primary">
                    {active.targetSourceAccession}
                    {active.method ? ` · ${active.method}` : ""}
                  </span>
                </div>
              )}

              <p className="text-xs text-content-muted">
                {active.evidenceType === "computational_target"
                  ? "This site was predicted by a Cas9 NGG scan of an authentic stored sequence. It is not experimental validation and does not mean an organism was edited. Efficiency scores are not invented."
                  : "Scores are provided by the source database. BIOWIKI does not compute or estimate efficiency or off-target values on the client."}
              </p>
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
