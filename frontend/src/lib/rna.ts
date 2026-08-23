import { baseColors, type BaseKey } from "@/lib/design-tokens";
import type { RnaClass, RnaSequence } from "@/types/rna";

export const RNA_CLASS_OPTIONS: { value: RnaClass | "all"; label: string }[] = [
  { value: "all", label: "All classes" },
  { value: "mrna", label: "mRNA" },
  { value: "trna", label: "tRNA" },
  { value: "rrna", label: "rRNA" },
  { value: "lncrna", label: "lncRNA" },
  { value: "mirna", label: "miRNA" },
  { value: "snrna", label: "snRNA" },
  { value: "other", label: "Other" },
];

export const CODING_OPTIONS: { value: "all" | "coding" | "noncoding"; label: string }[] = [
  { value: "all", label: "Coding & non-coding" },
  { value: "coding", label: "Coding" },
  { value: "noncoding", label: "Non-coding" },
];

export const RNA_SOURCE_OPTIONS: { value: string; label: string }[] = [
  { value: "all", label: "All sources" },
  { value: "ncbi_refseq", label: "NCBI RefSeq" },
  { value: "ncbi_genbank", label: "NCBI GenBank" },
  { value: "ensembl", label: "Ensembl" },
  { value: "ena", label: "ENA" },
];

export const RNA_CLASS_LABEL: Record<RnaClass, string> = {
  mrna: "mRNA",
  trna: "tRNA",
  rrna: "rRNA",
  lncrna: "lncRNA",
  mirna: "miRNA",
  snrna: "snRNA",
  other: "Other",
};

const grouping = new Intl.NumberFormat("en-US");

export function formatNt(length: number): string {
  return `${grouping.format(length)} nt`;
}

export function formatGc(gc: number | null): string {
  return gc === null ? "—" : `${(gc * 100).toFixed(1)}%`;
}

export function baseColor(base: string): string {
  const key = base.toUpperCase() as BaseKey;
  return baseColors[key] ?? baseColors.N;
}

/** Build a FASTA record from a sequence carrying real residues. */
export function toFasta(seq: RnaSequence, lineWidth = 70): string {
  const header = `>${seq.accession}${seq.version ? `.${seq.version}` : ""} ${seq.name} [${seq.organism}]`;
  if (!seq.sequence) return header;
  const lines: string[] = [];
  for (let i = 0; i < seq.sequence.length; i += lineWidth) {
    lines.push(seq.sequence.slice(i, i + lineWidth));
  }
  return `${header}\n${lines.join("\n")}`;
}

export function toJson(seq: RnaSequence): string {
  return JSON.stringify(seq, null, 2);
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

export interface RnaPageStat {
  id: string;
  value: number;
  suffix?: string;
  label: string;
}

/**
 * INSTITUTIONAL RNA FIGURES — interface only.
 * Isolated headline numbers, replaced by real `/statistics/rna` values later.
 * No sequences, accessions or organisms are fabricated.
 */
export const RNA_PAGE_STATS: RnaPageStat[] = [
  { id: "rna", value: 400_000, suffix: "+", label: "RNA sequences" },
  { id: "organisms", value: 200, suffix: "+", label: "Organisms" },
  { id: "classes", value: 6, label: "RNA classes" },
  { id: "formats", value: 3, label: "Export formats" },
];
