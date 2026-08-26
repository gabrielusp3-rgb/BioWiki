import { baseColors } from "@/lib/design-tokens";
import { AA_GROUP_COLOR, AA_GROUP_LABEL, aaGroup, type AaGroup } from "@/lib/protein";

/** Alphabet the viewer should colour and legend against. */
export type SequenceKind = "nucleotide" | "protein";

/** Nucleotide molecule — controls whether the legend shows T (DNA) or U (RNA). */
export type Molecule = "dna" | "rna";

/**
 * NCBI RefSeq stores mRNA/rRNA as a DNA alphabet (T). For RNA views, show U
 * without rewriting the stored record.
 */
export function rnaLetters(sequence: string): string {
  return sequence.replace(/T/g, "U").replace(/t/g, "u");
}

export interface LegendEntry {
  color: string;
  label: string;
}

/**
 * Nucleotide colouring (per BIOWIKI spec):
 * A → cyan, T → magenta, G → green, C → yellow. U mirrors T for RNA.
 */
export function nucleotideColor(base: string): string {
  const key = base.toUpperCase();
  return (baseColors as Record<string, string>)[key] ?? baseColors.N;
}

/** Amino acid colouring by physicochemical property group. */
export function aminoAcidColor(residue: string): string {
  return AA_GROUP_COLOR[aaGroup(residue)];
}

export function residueColor(residue: string, kind: SequenceKind): string {
  return kind === "protein" ? aminoAcidColor(residue) : nucleotideColor(residue);
}

export function legendFor(kind: SequenceKind, molecule: Molecule = "dna"): LegendEntry[] {
  if (kind === "protein") {
    return (Object.keys(AA_GROUP_COLOR) as AaGroup[]).map((group) => ({
      color: AA_GROUP_COLOR[group],
      label: AA_GROUP_LABEL[group],
    }));
  }
  const bases = molecule === "rna" ? (["A", "U", "G", "C"] as const) : (["A", "T", "G", "C"] as const);
  return bases.map((b) => ({ color: (baseColors as Record<string, string>)[b], label: b }));
}

/** Build a wrapped FASTA record from a header line and raw residues. */
export function buildFasta(header: string, sequence: string | null, lineWidth = 60): string {
  const headerLine = header.startsWith(">") ? header : `>${header}`;
  if (!sequence) return headerLine;
  const lines: string[] = [];
  for (let i = 0; i < sequence.length; i += lineWidth) {
    lines.push(sequence.slice(i, i + lineWidth));
  }
  return `${headerLine}\n${lines.join("\n")}`;
}

/** Trigger a client-side text download. */
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
