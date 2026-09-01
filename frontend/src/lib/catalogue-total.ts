import { formatStatistic } from "@/lib/statistics";

export type CatalogueLoadStatus = "idle" | "loading" | "success" | "error" | "unavailable";

export type CatalogueTotalDisplay =
  | { kind: "unavailable"; text: string }
  | { kind: "loading"; text: string }
  | { kind: "ready"; text: string; total: number };

/**
 * Visible catalogue total for category explorers.
 * Uses the list endpoint `total` (filtered when search/filters are active).
 * Never invents a marketing fallback.
 */
export function catalogueTotalDisplay(
  status: CatalogueLoadStatus,
  total: number,
  noun: string,
): CatalogueTotalDisplay {
  if (status === "unavailable" || status === "error") {
    return { kind: "unavailable", text: "Live counts unavailable" };
  }
  if ((status === "loading" || status === "idle") && total <= 0) {
    return { kind: "loading", text: "Loading catalogue total…" };
  }
  return {
    kind: "ready",
    text: `${formatStatistic(total)} ${noun}`,
    total,
  };
}
