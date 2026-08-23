import { baseColors, type BaseKey } from "@/lib/design-tokens";
import type { CasSystem, CrisprGuide } from "@/types/crispr";

export const CAS_SYSTEM_OPTIONS: { value: CasSystem | "all"; label: string }[] = [
  { value: "all", label: "All systems" },
  { value: "cas9", label: "Cas9" },
  { value: "cas12a", label: "Cas12a (Cpf1)" },
  { value: "cas13", label: "Cas13" },
  { value: "base_editor", label: "Base editor" },
  { value: "other", label: "Other" },
];

export const CAS_SYSTEM_LABEL: Record<CasSystem, string> = {
  cas9: "Cas9",
  cas12a: "Cas12a",
  cas13: "Cas13",
  base_editor: "Base editor",
  other: "Other",
};

export const CRISPR_SOURCE_OPTIONS: { value: string; label: string }[] = [
  { value: "all", label: "All sources" },
  { value: "ncbi_refseq", label: "NCBI RefSeq" },
  { value: "ensembl", label: "Ensembl" },
  { value: "ena", label: "ENA" },
];

const grouping = new Intl.NumberFormat("en-US");

export function formatNt(length: number): string {
  return `${grouping.format(length)} nt`;
}

/** Scores are provided by the backend; display only, never computed here. */
export function formatScore(score: number | null): string {
  return score === null ? "—" : score.toFixed(2);
}

export function baseColor(base: string): string {
  const key = base.toUpperCase() as BaseKey;
  return baseColors[key] ?? baseColors.N;
}

export function toFasta(guide: CrisprGuide, lineWidth = 70): string {
  const header = `>${guide.accession} ${guide.name} | ${CAS_SYSTEM_LABEL[guide.system]} | PAM:${guide.pam} | target:${guide.targetGene} [${guide.organism}]`;
  if (!guide.guideSequence) return header;
  const lines: string[] = [];
  for (let i = 0; i < guide.guideSequence.length; i += lineWidth) {
    lines.push(guide.guideSequence.slice(i, i + lineWidth));
  }
  return `${header}\n${lines.join("\n")}`;
}

export function toJson(guide: CrisprGuide): string {
  return JSON.stringify(guide, null, 2);
}

export function downloadText(filename: string, content: string, mime = "text/plain") {
  const blob = new Blob([content], { type: `${mime};charset=utf-8` });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

export interface CrisprPageStat {
  id: string;
  value: number;
  suffix?: string;
  label: string;
}

/**
 * INSTITUTIONAL CRISPR FIGURES — interface only.
 * Isolated headline numbers, replaced by real `/statistics/crispr` values later.
 * No guides, targets or organisms are fabricated.
 */
export const CRISPR_PAGE_STATS: CrisprPageStat[] = [
  { id: "crispr", value: 150_000, suffix: "+", label: "Guide RNAs" },
  { id: "organisms", value: 200, suffix: "+", label: "Organisms" },
  { id: "systems", value: 4, label: "Cas systems" },
  { id: "formats", value: 3, label: "Export formats" },
];
