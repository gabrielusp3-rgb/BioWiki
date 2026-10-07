"use client";

import { useLocale } from "@/lib/i18n/LocaleProvider";

export function SearchHeading() {
  const { t } = useLocale();
  return (
    <header className="mb-10 flex flex-col gap-4">
      <span className="eyebrow">{t("searchEyebrow")}</span>
      <h2 className="max-w-3xl text-balance font-display text-3xl font-bold uppercase tracking-tightest sm:text-4xl">
        {t("searchTitle")}
      </h2>
      <p className="max-w-2xl text-balance text-base leading-relaxed text-content-secondary">
        {t("searchDescription")}
      </p>
    </header>
  );
}
