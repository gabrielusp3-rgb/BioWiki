import { useId, type ReactNode } from "react";
import type { LocaleCode } from "@/lib/i18n/locales";

/** Painted circular flags. Emoji flags are unreadable on Windows. */
export function FlagMark({ code, size = 36 }: { code: LocaleCode; size?: number }) {
  const clipId = useId();
  return (
    <span
      aria-hidden
      className="inline-grid shrink-0 place-items-center rounded-full border border-white/30 bg-white/10 p-0.5 shadow-[inset_0_1px_0_rgba(255,255,255,0.35),0_4px_14px_rgba(0,0,0,0.28)]"
      style={{ width: size + 8, height: size + 8 }}
    >
      <svg
        width={size}
        height={size}
        viewBox="0 0 64 64"
        className="block rounded-full"
        role="img"
      >
        <defs>
          <clipPath id={clipId}>
            <circle cx="32" cy="32" r="32" />
          </clipPath>
        </defs>
        <g clipPath={`url(#${clipId})`}>{FLAG[code]}</g>
      </svg>
    </span>
  );
}

const FLAG: Record<LocaleCode, ReactNode> = {
  "pt-BR": (
    <>
      <rect width="64" height="64" fill="#009B3A" />
      <polygon points="32,8 58,32 32,56 6,32" fill="#FEDD00" />
      <circle cx="32" cy="32" r="11" fill="#002776" />
    </>
  ),
  "en-GB": (
    <>
      <rect width="64" height="64" fill="#012169" />
      <polygon points="0,0 14,0 64,50 64,64 50,64 0,14" fill="#fff" />
      <polygon points="64,0 50,0 0,50 0,64 14,64 64,14" fill="#fff" />
      <polygon points="0,0 8,0 64,56 64,64 56,64 0,8" fill="#C8102E" />
      <polygon points="64,0 56,0 0,56 0,64 8,64 64,8" fill="#C8102E" />
      <rect x="26" width="12" height="64" fill="#fff" />
      <rect y="26" width="64" height="12" fill="#fff" />
      <rect x="28" width="8" height="64" fill="#C8102E" />
      <rect y="28" width="64" height="8" fill="#C8102E" />
    </>
  ),
  "es-ES": (
    <>
      <rect width="64" height="64" fill="#AA151B" />
      <rect y="16" width="64" height="32" fill="#F1BF00" />
    </>
  ),
  "de-DE": (
    <>
      <rect width="64" height="22" fill="#000" />
      <rect y="22" width="64" height="20" fill="#DD0000" />
      <rect y="42" width="64" height="22" fill="#FFCE00" />
    </>
  ),
  "it-IT": (
    <>
      <rect width="22" height="64" fill="#009246" />
      <rect x="22" width="20" height="64" fill="#fff" />
      <rect x="42" width="22" height="64" fill="#CE2B37" />
    </>
  ),
  "zh-CN": (
    <>
      <rect width="64" height="64" fill="#DE2910" />
      <polygon points="18,12 20.2,18.6 27,18.6 21.4,22.6 23.6,29.2 18,25.2 12.4,29.2 14.6,22.6 9,18.6 15.8,18.6" fill="#FFDE00" />
    </>
  ),
  "ja-JP": (
    <>
      <rect width="64" height="64" fill="#fff" />
      <circle cx="32" cy="32" r="12" fill="#BC002D" />
    </>
  ),
  "ar-SA": (
    <>
      <rect width="64" height="64" fill="#006C35" />
      <rect x="14" y="30" width="36" height="4" rx="1" fill="#fff" />
    </>
  ),
  "fr-FR": (
    <>
      <rect width="22" height="64" fill="#0055A4" />
      <rect x="22" width="20" height="64" fill="#fff" />
      <rect x="42" width="22" height="64" fill="#EF4135" />
    </>
  ),
  "ru-RU": (
    <>
      <rect width="64" height="22" fill="#fff" />
      <rect y="22" width="64" height="20" fill="#0039A6" />
      <rect y="42" width="64" height="22" fill="#D52B1E" />
    </>
  ),
  "hi-IN": (
    <>
      <rect width="64" height="22" fill="#FF9933" />
      <rect y="22" width="64" height="20" fill="#fff" />
      <rect y="42" width="64" height="22" fill="#138808" />
      <circle cx="32" cy="32" r="6" fill="none" stroke="#000080" strokeWidth="1.6" />
    </>
  ),
};
