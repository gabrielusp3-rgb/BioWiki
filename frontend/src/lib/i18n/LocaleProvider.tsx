"use client";

import { useRouter } from "next/navigation";
import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { MESSAGES, type MessageKey } from "@/lib/i18n/messages";
import { chromeText, type ChromeKey } from "@/lib/i18n/chrome";
import { surfaceText, type SurfaceKey } from "@/lib/i18n/surface";
import {
  DEFAULT_LOCALE,
  LOCALE_COOKIE,
  directionOf,
  parseLocale,
  type LocaleCode,
} from "@/lib/i18n/locales";

interface LocaleContextValue {
  locale: LocaleCode;
  setLocale: (locale: LocaleCode) => void;
  t: (key: MessageKey | SurfaceKey | ChromeKey) => string;
  dir: "ltr" | "rtl";
}

const LocaleContext = createContext<LocaleContextValue | null>(null);

function writeLocaleCookie(locale: LocaleCode) {
  document.cookie = `${LOCALE_COOKIE}=${locale}; Path=/; Max-Age=31536000; SameSite=Lax`;
}

function applyDocumentLocale(locale: LocaleCode) {
  document.documentElement.lang = locale;
  document.documentElement.dir = directionOf(locale);
}

function lookup(locale: LocaleCode, key: MessageKey | SurfaceKey | ChromeKey): string {
  if (key in MESSAGES[locale]) return MESSAGES[locale][key as MessageKey];
  if (key in CHROME_KEYS) return chromeText(locale, key as ChromeKey);
  return surfaceText(locale, key as SurfaceKey);
}

const CHROME_KEYS = new Set<string>([
  "aboutEyebrow",
  "aboutTitle",
  "aboutLead",
  "aboutP1",
  "aboutP2",
  "aboutP3",
  "licenseEyebrow",
  "licenseTitle",
  "licenseLead",
  "licenseConnectors",
  "licenseRelated",
  "srcNcbi",
  "srcUniprot",
  "srcEnsembl",
  "srcPdb",
  "srcEna",
  "srcRfam",
  "srcDdbj",
  "docsEyebrow",
  "docsTitle",
  "docsLead",
  "docsBrowse",
  "docsBrowseBody",
  "docsApi",
  "docsApiBody",
  "docsIntegrity",
  "docsIntegrityBody",
  "docsExport",
  "docsExportBody",
  "introEyebrow",
  "introTitle",
  "introDescription",
  "globalEyebrow",
  "globalTitle",
  "phExample",
  "phProteins",
  "phRna",
  "phPublications",
  "phOrganisms",
  "phSearchBar",
  "close",
  "fullscreen",
  "closeDialog",
  "profileSections",
  "sourceNarrative",
  "sourceNarrativeNote",
]);

export function LocaleProvider({
  initialLocale,
  children,
}: {
  initialLocale?: string | null;
  children: React.ReactNode;
}) {
  const router = useRouter();
  const [locale, setLocaleState] = useState<LocaleCode>(parseLocale(initialLocale));

  useEffect(() => {
    applyDocumentLocale(locale);
  }, [locale]);

  const value = useMemo<LocaleContextValue>(() => {
    return {
      locale,
      dir: directionOf(locale),
      t: (key) => lookup(locale, key),
      setLocale: (next) => {
        const parsed = parseLocale(next);
        setLocaleState(parsed);
        writeLocaleCookie(parsed);
        applyDocumentLocale(parsed);
        router.refresh();
      },
    };
  }, [locale, router]);

  return <LocaleContext.Provider value={value}>{children}</LocaleContext.Provider>;
}

export function useLocale(): LocaleContextValue {
  const value = useContext(LocaleContext);
  if (value) return value;
  return {
    locale: DEFAULT_LOCALE,
    dir: "ltr",
    t: (key) => lookup(DEFAULT_LOCALE, key),
    setLocale: () => undefined,
  };
}
