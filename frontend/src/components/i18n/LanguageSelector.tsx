"use client";

import { useEffect, useId, useRef, useState } from "react";
import { LOCALES, localeMeta } from "@/lib/i18n/locales";
import { useLocale } from "@/lib/i18n/LocaleProvider";

function FlagDisc({ flag }: { flag: string }) {
  return (
    <span
      aria-hidden
      className="grid h-7 w-7 shrink-0 place-items-center rounded-full border border-white/25 bg-white/[0.04] shadow-[inset_0_1px_0_rgba(255,255,255,0.18)]"
    >
      <span className="grid h-5 w-5 place-items-center overflow-hidden rounded-full text-[15px] leading-none">
        {flag}
      </span>
    </span>
  );
}

export function LanguageSelector() {
  const { locale, setLocale, t } = useLocale();
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const listId = useId();
  const current = localeMeta(locale);

  useEffect(() => {
    if (!open) return;
    const onPointer = (event: MouseEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) setOpen(false);
    };
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onPointer);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onPointer);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  return (
    <div ref={rootRef} className="relative">
      <button
        type="button"
        data-testid="language-selector"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={listId}
        aria-label={`${t("languageMenu")}: ${current.name}`}
        onClick={() => setOpen((value) => !value)}
        className="flex h-10 items-center gap-2 rounded-full border border-white/15 bg-white/[0.06] px-2 pe-3 text-content-primary shadow-[0_8px_24px_rgba(0,0,0,0.25)] backdrop-blur-md transition-colors hover:border-white/30 hover:bg-white/[0.1]"
      >
        <FlagDisc flag={current.flag} />
        <span className="max-w-[5.5rem] truncate font-display text-[11px] font-medium tracking-wide sm:max-w-none">
          {current.name}
        </span>
      </button>
      {open && (
        <ul
          id={listId}
          role="listbox"
          aria-label={t("languageMenu")}
          data-testid="language-menu"
          className="absolute end-0 z-[260] mt-2 max-h-[min(70vh,28rem)] w-56 overflow-auto rounded-2xl border border-white/15 bg-black/55 p-1.5 shadow-[0_16px_40px_rgba(0,0,0,0.45)] backdrop-blur-xl"
        >
          {LOCALES.map((item) => {
            const selected = item.code === locale;
            return (
              <li key={item.code} role="presentation">
                <button
                  type="button"
                  role="option"
                  aria-selected={selected}
                  data-testid={`locale-${item.code}`}
                  onClick={() => {
                    setLocale(item.code);
                    setOpen(false);
                  }}
                  className={`flex w-full items-center gap-2 rounded-full px-1.5 py-1.5 text-start text-sm transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-cyan-300 ${
                    selected
                      ? "bg-white/10 text-content-primary"
                      : "text-content-secondary hover:bg-white/[0.06] hover:text-content-primary"
                  }`}
                >
                  <FlagDisc flag={item.flag} />
                  <span className="truncate">{item.name}</span>
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
