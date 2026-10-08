"use client";

import { useEffect, useId, useRef, useState } from "react";
import { FlagMark } from "@/components/i18n/FlagMark";
import { LOCALES, localeMeta } from "@/lib/i18n/locales";
import { useLocale } from "@/lib/i18n/LocaleProvider";

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

  function move(from: number, delta: number) {
    const next = (from + delta + LOCALES.length) % LOCALES.length;
    setLocale(LOCALES[next].code);
  }

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
        onKeyDown={(event) => {
          if (event.key === "ArrowDown" || event.key === "ArrowUp") {
            event.preventDefault();
            setOpen(true);
            const index = LOCALES.findIndex((item) => item.code === locale);
            move(index, event.key === "ArrowDown" ? 1 : -1);
          }
        }}
        className="grid h-11 w-11 place-items-center rounded-full border border-transparent bg-transparent text-content-primary transition duration-200 hover:bg-white/[0.06] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-cyan-300 motion-reduce:transition-none"
      >
        <FlagMark code={current.code} size={26} />
      </button>
      {open && (
        <ul
          id={listId}
          role="listbox"
          aria-label={t("languageMenu")}
          data-testid="language-menu"
          className="absolute end-0 z-[260] mt-2 max-h-[min(70dvh,26rem)] w-56 origin-top overflow-auto rounded-xl border border-white/15 bg-black/55 p-1.5 shadow-[inset_0_1px_0_rgba(255,255,255,0.16),0_18px_40px_rgba(0,0,0,0.45)] backdrop-blur-xl"
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
                  className={`flex w-full items-center gap-3 rounded-lg px-2 py-1.5 text-start text-sm transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-cyan-300 motion-reduce:transition-none ${
                    selected
                      ? "bg-white/12 text-content-primary shadow-[inset_0_0_0_1px_rgba(0,242,255,0.28)]"
                      : "text-content-secondary hover:bg-white/[0.06] hover:text-content-primary"
                  }`}
                >
                  <FlagMark code={item.code} size={28} />
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
