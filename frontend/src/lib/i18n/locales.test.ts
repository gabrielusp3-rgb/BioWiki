import { describe, expect, it } from "vitest";
import { MESSAGES, type MessageKey } from "@/lib/i18n/messages";
import { DEFAULT_LOCALE, LOCALES, directionOf, parseLocale } from "@/lib/i18n/locales";

describe("locales", () => {
  it("exposes exactly the eleven production languages, including English", () => {
    expect(LOCALES.map((locale) => locale.code)).toEqual([
      "pt-BR",
      "en-GB",
      "es-ES",
      "de-DE",
      "it-IT",
      "zh-CN",
      "ja-JP",
      "ar-SA",
      "fr-FR",
      "ru-RU",
      "hi-IN",
    ]);
    expect(DEFAULT_LOCALE).toBe("en-GB");
    expect(directionOf("ar-SA")).toBe("rtl");
    expect(directionOf("en-GB")).toBe("ltr");
  });

  it("rejects arbitrary locale values", () => {
    expect(parseLocale("../en")).toBe("en-GB");
    expect(parseLocale("pt-BR")).toBe("pt-BR");
  });

  it("gives every locale the same interface keys and keeps English labels stable", () => {
    const keys = Object.keys(MESSAGES["en-GB"]) as MessageKey[];
    for (const locale of LOCALES) {
      expect(Object.keys(MESSAGES[locale.code]).sort()).toEqual([...keys].sort());
    }
    expect(MESSAGES["en-GB"].searchInputLabel).toBe("Search catalogue");
    expect(MESSAGES["en-GB"].statsOrganismsTracked).toBe("Organisms tracked (database)");
    expect(MESSAGES["en-GB"].stateLiveCountsUnavailable).toBe("Live counts unavailable");
  });
});
