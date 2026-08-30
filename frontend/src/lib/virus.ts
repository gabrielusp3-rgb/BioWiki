import { baseColors, type BaseKey } from "@/lib/design-tokens";
import type { GenomeType, VirusSequence } from "@/types/virus";

export const GENOME_TYPE_OPTIONS: { value: GenomeType | "all"; label: string }[] = [
  { value: "all", label: "All genome types" },
  { value: "dsDNA", label: "dsDNA" },
  { value: "ssDNA", label: "ssDNA" },
  { value: "dsRNA", label: "dsRNA" },
  { value: "ssRNA+", label: "ssRNA (+)" },
  { value: "ssRNA-", label: "ssRNA (−)" },
  { value: "ssRNA-RT", label: "ssRNA-RT" },
  { value: "dsDNA-RT", label: "dsDNA-RT" },
  { value: "other", label: "Other" },
];

export const VIRUS_SOURCE_OPTIONS: { value: string; label: string }[] = [
  { value: "all", label: "All sources" },
  { value: "ncbi_refseq", label: "NCBI RefSeq" },
  { value: "ncbi_genbank", label: "NCBI GenBank" },
  { value: "ena", label: "ENA" },
];

const grouping = new Intl.NumberFormat("en-US");

export function formatBases(seq: VirusSequence): string {
  const unit = seq.molecule === "rna" ? "nt" : "bp";
  return `${grouping.format(seq.length)} ${unit}`;
}

export function formatLength(length: number): string {
  return grouping.format(length);
}

export function baseColor(base: string): string {
  const key = base.toUpperCase() as BaseKey;
  return baseColors[key] ?? baseColors.N;
}

export function toFasta(seq: VirusSequence, lineWidth = 70): string {
  const header = `>${seq.accession}${seq.version ? `.${seq.version}` : ""} ${seq.name} | ${seq.family}${seq.segment ? ` | segment ${seq.segment}` : ""} [${seq.organism}]`;
  if (!seq.sequence) return header;
  const lines: string[] = [];
  for (let i = 0; i < seq.sequence.length; i += lineWidth) {
    lines.push(seq.sequence.slice(i, i + lineWidth));
  }
  return `${header}\n${lines.join("\n")}`;
}

export function toJson(seq: VirusSequence): string {
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

