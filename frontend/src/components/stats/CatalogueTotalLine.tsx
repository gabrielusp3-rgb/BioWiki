"use client";

import { catalogueTotalDisplay, type CatalogueLoadStatus } from "@/lib/catalogue-total";

export function CatalogueTotalLine({
  status,
  total,
  noun,
}: {
  status: CatalogueLoadStatus;
  total: number;
  noun: string;
}) {
  const display = catalogueTotalDisplay(status, total, noun);
  const muted = display.kind !== "ready";

  return (
    <p
      role="status"
      data-testid="catalogue-list-total"
      className={
        muted
          ? "font-display text-sm font-semibold uppercase tracking-wide text-content-muted"
          : "font-display text-2xl font-bold tracking-tightest tabular-nums text-content-primary sm:text-3xl"
      }
    >
      {display.text}
    </p>
  );
}
