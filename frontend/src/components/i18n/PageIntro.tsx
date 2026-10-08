"use client";

import { useLocale } from "@/lib/i18n/LocaleProvider";
import type { SurfaceKey } from "@/lib/i18n/surface";

export function PageIntro({
  eyebrow,
  title,
  description,
}: {
  eyebrow: SurfaceKey;
  title: SurfaceKey;
  description?: SurfaceKey;
}) {
  const { t } = useLocale();
  return (
    <header className="mb-10 flex flex-col gap-4">
      <span className="eyebrow">{t(eyebrow)}</span>
      <h2 className="max-w-3xl text-balance font-display text-3xl font-bold uppercase tracking-tightest sm:text-4xl">
        {t(title)}
      </h2>
      {description ? (
        <p className="max-w-2xl text-balance text-base leading-relaxed text-content-secondary">
          {t(description)}
        </p>
      ) : null}
    </header>
  );
}
