import { describe, expect, it } from "vitest";
import { CHROME } from "@/lib/i18n/chrome";
import { LOCALES } from "@/lib/i18n/locales";
import { lookup } from "@/lib/i18n/lookup";

const MUST_LOCALIZE = [
  "aboutTitle",
  "licenseTitle",
  "docsTitle",
  "introTitle",
  "globalTitle",
  "close",
  "sourceNarrative",
] as const;

describe("chrome translations", () => {
  it("does not leave the main page titles in English for the other ten locales", () => {
    for (const locale of LOCALES) {
      if (locale.code === "en-GB") continue;
      for (const key of MUST_LOCALIZE) {
        expect(CHROME[locale.code][key], `${locale.code} ${key}`).not.toBe(CHROME["en-GB"][key]);
      }
    }
  });

  it("resolves chrome copy that is not a navigation message", () => {
    expect(lookup("en-GB", "introTitle")).toBe("Archaic introgression in living humans");
    expect(lookup("es-ES", "aboutEyebrow")).toBe("Acerca de");
    expect(lookup("pt-BR", "introTitle").length).toBeGreaterThan(0);
    expect(lookup("en-GB", "languageMenu")).toBe("Language");
  });

  it("keeps Homo sapiens as an identifier inside the example placeholder", () => {
    for (const locale of LOCALES) {
      expect(CHROME[locale.code].phExample).toContain("Homo sapiens");
    }
  });
});
