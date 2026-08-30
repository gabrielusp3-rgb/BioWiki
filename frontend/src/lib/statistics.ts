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

/** Catalogue counts must come from `/statistics`. Never invent scale figures. */

const grouping = new Intl.NumberFormat("en-US");

/** Format a statistic value with thousands grouping and its optional suffix. */
export function formatStatistic(value: number, suffix = ""): string {
  return `${grouping.format(Math.round(value))}${suffix}`;
}
