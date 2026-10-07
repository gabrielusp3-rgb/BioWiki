"use client";

import { useLocale } from "@/lib/i18n/LocaleProvider";

/** Shown instead of fabricated scale figures when `/statistics` is unreachable. */
export function LiveCountsUnavailable({ detail }: { detail?: string }) {
  const { t } = useLocale();
  return (
    <div className="glass hairline p-6" data-testid="live-counts-unavailable">
      <p className="font-display text-sm font-semibold uppercase tracking-wide text-content-primary">
        {t("stateLiveCountsUnavailable")}
      </p>
      <p className="mt-2 text-sm leading-relaxed text-content-secondary">
        {detail ?? t("stateLiveCountsDetail")}
      </p>
    </div>
  );
}
