import { baseColors, type BaseKey } from "@/lib/design-tokens";
import type { DnaMoleculeType, DnaSequence, Strand } from "@/types/dna";

export const MOLECULE_TYPE_OPTIONS: { value: DnaMoleculeType | "all"; label: string }[] = [
  { value: "all", label: "All types" },
  { value: "gene", label: "Gene" },
  { value: "cds", label: "CDS" },
  { value: "genomic", label: "Genomic" },
  { value: "mrna", label: "mRNA" },
  { value: "exon", label: "Exon" },
  { value: "regulatory", label: "Regulatory" },
  { value: "other", label: "Other" },
];

export const STRAND_OPTIONS: { value: Strand | "all"; label: string }[] = [
  { value: "all", label: "Any strand" },
  { value: "+", label: "Forward (+)" },
  { value: "-", label: "Reverse (−)" },
  { value: "unknown", label: "Unknown" },
];

export const DNA_SOURCE_OPTIONS: { value: string; label: string }[] = [
  { value: "all", label: "All sources" },
  { value: "ncbi_genbank", label: "NCBI GenBank" },
  { value: "ncbi_refseq", label: "NCBI RefSeq" },
  { value: "ensembl", label: "Ensembl" },
  { value: "ena", label: "ENA" },
];

export const MOLECULE_TYPE_LABEL: Record<DnaMoleculeType, string> = {
  gene: "Gene",
  cds: "CDS",
  genomic: "Genomic",
  mrna: "mRNA",
  exon: "Exon",
  regulatory: "Regulatory",
  other: "Other",
};

const grouping = new Intl.NumberFormat("en-US");

export function formatBp(length: number): string {
  return `${grouping.format(length)} bp`;
}

export function formatGc(gc: number | null): string {
  return gc === null ? "—" : `${(gc * 100).toFixed(1)}%`;
}

export function baseColor(base: string): string {
  const key = base.toUpperCase() as BaseKey;
  return baseColors[key] ?? baseColors.N;
}

/** Build a FASTA record from a sequence that already carries real residues. */
export function toFasta(seq: DnaSequence, lineWidth = 70): string {
  const header = `>${seq.accession}${seq.version ? `.${seq.version}` : ""} ${seq.name} [${seq.organism}]`;
  if (!seq.sequence) return header;
  const lines: string[] = [];
  for (let i = 0; i < seq.sequence.length; i += lineWidth) {
    lines.push(seq.sequence.slice(i, i + lineWidth));
  }
  return `${header}\n${lines.join("\n")}`;
}

export function toJson(seq: DnaSequence): string {
  return JSON.stringify(seq, null, 2);
}

/** Trigger a client-side download of in-memory (real) content. */
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

