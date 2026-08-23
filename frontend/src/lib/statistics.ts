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
  { id: "organisms", value: 200, suffix: "+", label: "Organisms" },
  { id: "proteins", value: 500_000, suffix: "+", label: "Proteins", category: "protein" },
  { id: "rna", value: 400_000, suffix: "+", label: "RNA", category: "rna" },
  { id: "dna", value: 500_000, suffix: "+", label: "DNA", category: "dna" },
  { id: "crispr", value: 150_000, suffix: "+", label: "CRISPR", category: "crispr" },
];

const grouping = new Intl.NumberFormat("en-US");

/** Format a statistic value with thousands grouping and its optional suffix. */
export function formatStatistic(value: number, suffix = ""): string {
  return `${grouping.format(Math.round(value))}${suffix}`;
}
