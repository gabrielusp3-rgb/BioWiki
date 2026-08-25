"use client";

import { useMemo } from "react";
import { residueColor, type SequenceKind } from "@/lib/sequence-colors";

const grouping = new Intl.NumberFormat("en-US");

export interface SequenceHighlightProps {
  sequence: string;
  kind: SequenceKind;
  /** Residues per rendered line. */
  lineWidth?: number;
  /** Hard cap on rendered residues to keep the DOM light for huge genomes. */
  renderCap?: number;
  showLineNumbers?: boolean;
}

/**
 * Renders a residue sequence with per-character syntax highlighting and
 * optional gutter line numbers. Rendering is capped so multi-megabase genomes
 * never freeze the browser — the full record is always available via download.
 */
export function SequenceHighlight({
  sequence,
  kind,
  lineWidth = 60,
  renderCap = 12_000,
  showLineNumbers = true,
}: SequenceHighlightProps) {
  const { lines, truncated } = useMemo(() => {
    const capped = sequence.slice(0, renderCap);
    const rows: string[] = [];
    for (let i = 0; i < capped.length; i += lineWidth) {
      rows.push(capped.slice(i, i + lineWidth));
    }
    return { lines: rows, truncated: sequence.length > renderCap };
  }, [sequence, lineWidth, renderCap]);

  return (
    <div className="overflow-x-auto font-mono text-[13px] leading-6">
      {lines.map((line, rowIndex) => (
        <div key={rowIndex} className="flex min-w-0 gap-4">
          {showLineNumbers && (
            <span className="w-16 shrink-0 select-none text-right text-content-muted">
              {rowIndex * lineWidth + 1}
            </span>
          )}
          <span className="min-w-0 whitespace-pre tracking-[0.08em]">
            {line.split("").map((residue, i) => (
              <span key={i} style={{ color: residueColor(residue, kind) }}>
                {residue}
              </span>
            ))}
          </span>
        </div>
      ))}
      {truncated && (
        <p className="mt-4 text-xs text-content-muted">
          Showing first {grouping.format(renderCap)} of {grouping.format(sequence.length)}{" "}
          residues. Download the full record to view everything.
        </p>
      )}
    </div>
  );
}
