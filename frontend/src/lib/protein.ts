import type { ProteinSequence } from "@/types/protein";

export const PROTEIN_SOURCE_OPTIONS: { value: string; label: string }[] = [
  { value: "all", label: "All sources" },
  { value: "uniprot", label: "UniProt" },
  { value: "ncbi_refseq", label: "NCBI RefSeq" },
  { value: "pdb", label: "Protein Data Bank" },
];

export const REVIEWED_OPTIONS: { value: "all" | "reviewed" | "unreviewed"; label: string }[] = [
  { value: "all", label: "Reviewed & unreviewed" },
  { value: "reviewed", label: "Reviewed (Swiss-Prot)" },
  { value: "unreviewed", label: "Unreviewed (TrEMBL)" },
];

export const STRUCTURE_OPTIONS: { value: "all" | "with" | "without"; label: string }[] = [
  { value: "all", label: "Any structure" },
  { value: "with", label: "With 3D structure" },
  { value: "without", label: "Without structure" },
];

/** Amino acid property groups used for residue colouring. */
export type AaGroup = "hydrophobic" | "polar" | "acidic" | "basic" | "special";

export const AA_GROUP_COLOR: Record<AaGroup, string> = {
  hydrophobic: "#FFFF00",
  polar: "#39FF14",
  acidic: "#FF4444",
  basic: "#00F2FF",
  special: "#7C5CFF",
};

export const AA_GROUP_LABEL: Record<AaGroup, string> = {
  hydrophobic: "Hydrophobic",
  polar: "Polar",
  acidic: "Acidic",
  basic: "Basic",
  special: "Special",
};

const AA_TO_GROUP: Record<string, AaGroup> = {
  A: "hydrophobic", V: "hydrophobic", L: "hydrophobic", I: "hydrophobic",
  M: "hydrophobic", F: "hydrophobic", W: "hydrophobic",
  S: "polar", T: "polar", N: "polar", Q: "polar", Y: "polar",
  D: "acidic", E: "acidic",
  K: "basic", R: "basic", H: "basic",
  G: "special", P: "special", C: "special",
};

export function aaGroup(residue: string): AaGroup {
  return AA_TO_GROUP[residue.toUpperCase()] ?? "special";
}

export function aaColor(residue: string): string {
  return AA_GROUP_COLOR[aaGroup(residue)];
}

const grouping = new Intl.NumberFormat("en-US");

export function formatAa(length: number): string {
  return `${grouping.format(length)} aa`;
}

export function formatMw(mw: number | null): string {
  return mw === null ? "—" : `${(mw / 1000).toFixed(1)} kDa`;
}

/** RCSB Protein Data Bank structure URL for a PDB id. */
export function pdbUrl(pdbId: string): string {
  return `https://www.rcsb.org/structure/${encodeURIComponent(pdbId)}`;
}

export function toFasta(seq: ProteinSequence, lineWidth = 60): string {
  const header = `>${seq.accession} ${seq.name}${seq.gene ? ` GN=${seq.gene}` : ""} [${seq.organism}]`;
  if (!seq.sequence) return header;
  const lines: string[] = [];
  for (let i = 0; i < seq.sequence.length; i += lineWidth) {
    lines.push(seq.sequence.slice(i, i + lineWidth));
  }
  return `${header}\n${lines.join("\n")}`;
}

export function toJson(seq: ProteinSequence): string {
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

export interface ProteinPageStat {
  id: string;
  value: number;
  suffix?: string;
  label: string;
}

/**
 * INSTITUTIONAL PROTEIN FIGURES — interface only.
 * Isolated headline numbers, replaced by real `/statistics/proteins` values
 * later. No sequences, accessions or organisms are fabricated.
 */
export const PROTEIN_PAGE_STATS: ProteinPageStat[] = [
  { id: "proteins", value: 500_000, suffix: "+", label: "Proteins" },
  { id: "organisms", value: 200, suffix: "+", label: "Organisms" },
  { id: "sources", value: 3, label: "Public sources" },
  { id: "formats", value: 3, label: "Export formats" },
];
