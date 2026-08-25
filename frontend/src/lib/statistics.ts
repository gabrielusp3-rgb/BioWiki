import type { CategoryKey } from "@/lib/design-tokens";

export interface Statistic {
  id: string;
  /** Numeric value driving the count-up. Replace with real API data later. */
  value: number;
  /** Suffix appended after the formatted value (e.g. "+"). */
  suffix?: string;
  label: string;
  category?: CategoryKey;
}

/**
 * INSTITUTIONAL SCALE FIGURES — interface only.
 *
 * These are headline capacity numbers shown in the UI, NOT scientific records.
 * They are intentionally isolated here so they can be swapped for values served
 * by the backend `/statistics` endpoint (real counts) without touching any
 * component. No fabricated sequences, organisms or accessions are involved.
 */
export const INSTITUTIONAL_STATISTICS: Statistic[] = [
  { id: "sequences", value: 1_500_000, suffix: "+", label: "Sequences" },
  { id: "dna", value: 500_000, suffix: "+", label: "DNA", category: "dna" },
  { id: "rna", value: 400_000, suffix: "+", label: "RNA", category: "rna" },
  { id: "proteins", value: 500_000, suffix: "+", label: "Proteins", category: "protein" },
  { id: "crispr", value: 150_000, suffix: "+", label: "CRISPR", category: "crispr" },
  { id: "virus", value: 120_000, suffix: "+", label: "Virus", category: "virus" },
  { id: "publications", value: 1_000_000, suffix: "+", label: "Publications" },
  { id: "organisms", value: 200, suffix: "+", label: "Organisms" },
  { id: "genomes", value: 50_000, suffix: "+", label: "Genome assemblies", category: "genome" },
];

const grouping = new Intl.NumberFormat("en-US");

/** Format a statistic value with thousands grouping and its optional suffix. */
export function formatStatistic(value: number, suffix = ""): string {
  return `${grouping.format(Math.round(value))}${suffix}`;
}
