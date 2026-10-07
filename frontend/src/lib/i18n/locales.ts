export const LOCALE_COOKIE = "biowiki_locale";

export const LOCALES = [
  { code: "pt-BR", name: "Português", flag: "🇧🇷", dir: "ltr" },
  { code: "en-GB", name: "English", flag: "🇬🇧", dir: "ltr" },
  { code: "es-ES", name: "Español", flag: "🇪🇸", dir: "ltr" },
  { code: "de-DE", name: "Deutsch", flag: "🇩🇪", dir: "ltr" },
  { code: "it-IT", name: "Italiano", flag: "🇮🇹", dir: "ltr" },
  { code: "zh-CN", name: "中文", flag: "🇨🇳", dir: "ltr" },
  { code: "ja-JP", name: "日本語", flag: "🇯🇵", dir: "ltr" },
  { code: "ar-SA", name: "العربية", flag: "🇸🇦", dir: "rtl" },
  { code: "fr-FR", name: "Français", flag: "🇫🇷", dir: "ltr" },
  { code: "ru-RU", name: "Русский", flag: "🇷🇺", dir: "ltr" },
  { code: "hi-IN", name: "हिन्दी", flag: "🇮🇳", dir: "ltr" },
] as const;

export type LocaleCode = (typeof LOCALES)[number]["code"];
export type LocaleDirection = "ltr" | "rtl";

export const DEFAULT_LOCALE: LocaleCode = "en-GB";

const CODES = new Set<string>(LOCALES.map((locale) => locale.code));

export function isLocale(value: string | null | undefined): value is LocaleCode {
  return Boolean(value && CODES.has(value));
}

export function parseLocale(value: string | null | undefined): LocaleCode {
  return isLocale(value) ? value : DEFAULT_LOCALE;
}

export function localeMeta(code: LocaleCode) {
  const meta = LOCALES.find((locale) => locale.code === code);
  if (!meta) return LOCALES[1];
  return meta;
}

export function directionOf(code: LocaleCode): LocaleDirection {
  return localeMeta(code).dir;
}

export function readLocaleCookie(cookieHeader: string | null | undefined): LocaleCode {
  if (!cookieHeader) return DEFAULT_LOCALE;
  const parts = cookieHeader.split(";").map((part) => part.trim());
  const match = parts.find((part) => part.startsWith(`${LOCALE_COOKIE}=`));
  return parseLocale(match?.slice(LOCALE_COOKIE.length + 1));
}
