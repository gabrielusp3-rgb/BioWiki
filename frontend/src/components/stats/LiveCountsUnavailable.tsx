"use client";

/** Shown instead of fabricated scale figures when `/statistics` is unreachable. */
export function LiveCountsUnavailable({
  detail = "Real catalogue totals come from the live API. Scale placeholders are not shown.",
}: {
  detail?: string;
}) {
  return (
    <div className="glass hairline p-6" data-testid="live-counts-unavailable">
      <p className="font-display text-sm font-semibold uppercase tracking-wide text-content-primary">
        Live counts unavailable
      </p>
      <p className="mt-2 text-sm leading-relaxed text-content-secondary">{detail}</p>
    </div>
  );
}
