"use client";

import type { ReactNode } from "react";
import { cn } from "@/lib/cn";
import {
  CheckIcon,
  CollapseIcon,
  CopyIcon,
  DownloadIcon,
  ExpandIcon,
} from "@/components/ui/Icons";
import type { LegendEntry } from "@/lib/sequence-colors";

interface ToolButtonProps {
  onClick: () => void;
  disabled?: boolean;
  label: string;
  children: ReactNode;
}

function ToolButton({ onClick, disabled, label, children }: ToolButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      aria-label={label}
      title={label}
      className={cn(
        "inline-flex h-9 items-center gap-2 border border-glass-border px-3",
        "font-display text-xs font-semibold uppercase tracking-wide text-content-secondary",
        "transition-colors hover:border-white/30 hover:text-content-primary",
        "disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:border-glass-border disabled:hover:text-content-secondary",
      )}
    >
      {children}
    </button>
  );
}

export interface SequenceToolbarProps {
  legend: LegendEntry[];
  copied: boolean;
  canExport: boolean;
  onCopy: () => void;
  onDownloadFasta: () => void;
  onDownloadJson?: () => void;
  fullscreen?: boolean;
  onToggleFullscreen?: () => void;
}

export function SequenceToolbar({
  legend,
  copied,
  canExport,
  onCopy,
  onDownloadFasta,
  onDownloadJson,
  fullscreen,
  onToggleFullscreen,
}: SequenceToolbarProps) {
  return (
    <div className="flex flex-col gap-3 border-b border-glass-divider px-6 py-4 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex flex-wrap items-center gap-3">
        <span className="eyebrow">FASTA</span>
        <span className="h-4 w-px bg-glass-divider" aria-hidden />
        <div className="flex flex-wrap items-center gap-3">
          {legend.map((entry) => (
            <span key={entry.label} className="flex items-center gap-1.5">
              <span className="h-2.5 w-2.5" style={{ backgroundColor: entry.color }} />
              <span className="font-mono text-xs text-content-secondary">{entry.label}</span>
            </span>
          ))}
        </div>
      </div>

      <div className="flex items-center gap-2">
        <ToolButton onClick={onCopy} disabled={!canExport} label="Copy FASTA">
          {copied ? <CheckIcon className="h-4 w-4" /> : <CopyIcon className="h-4 w-4" />}
          {copied ? "Copied" : "Copy"}
        </ToolButton>
        <ToolButton onClick={onDownloadFasta} disabled={!canExport} label="Download FASTA">
          <DownloadIcon className="h-4 w-4" />
          FASTA
        </ToolButton>
        {onDownloadJson && (
          <ToolButton onClick={onDownloadJson} label="Download JSON">
            <DownloadIcon className="h-4 w-4" />
            JSON
          </ToolButton>
        )}
        {onToggleFullscreen && (
          <ToolButton
            onClick={onToggleFullscreen}
            label={fullscreen ? "Exit fullscreen" : "Fullscreen"}
          >
            {fullscreen ? (
              <CollapseIcon className="h-4 w-4" />
            ) : (
              <ExpandIcon className="h-4 w-4" />
            )}
          </ToolButton>
        )}
      </div>
    </div>
  );
}
