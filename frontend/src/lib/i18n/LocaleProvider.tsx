"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { MESSAGES, type MessageKey } from "@/lib/i18n/messages";
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
  t: (key: MessageKey) => string;
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

export function LocaleProvider({
  initialLocale,
  children,
}: {
  initialLocale?: string | null;
  children: React.ReactNode;
}) {
  const [locale, setLocaleState] = useState<LocaleCode>(parseLocale(initialLocale));

  useEffect(() => {
    applyDocumentLocale(locale);
  }, [locale]);

  const value = useMemo<LocaleContextValue>(() => {
    return {
      locale,
      dir: directionOf(locale),
      t: (key) => MESSAGES[locale][key],
      setLocale: (next) => {
        const parsed = parseLocale(next);
        setLocaleState(parsed);
        writeLocaleCookie(parsed);
        applyDocumentLocale(parsed);
      },
    };
  }, [locale]);

  return <LocaleContext.Provider value={value}>{children}</LocaleContext.Provider>;
}

export function useLocale(): LocaleContextValue {
  const value = useContext(LocaleContext);
  if (value) return value;
  return {
    locale: DEFAULT_LOCALE,
    dir: "ltr",
    t: (key) => MESSAGES[DEFAULT_LOCALE][key],
    setLocale: () => undefined,
  };
}
