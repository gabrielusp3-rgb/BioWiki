import { chromeText, type ChromeKey } from "@/lib/i18n/chrome";
import { type LocaleCode } from "@/lib/i18n/locales";
import { MESSAGES, type MessageKey } from "@/lib/i18n/messages";
import { surfaceText, type SurfaceKey } from "@/lib/i18n/surface";

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

export function lookup(locale: LocaleCode, key: MessageKey | SurfaceKey | ChromeKey): string {
  const messages = MESSAGES[locale] as Record<string, string>;
  if (Object.prototype.hasOwnProperty.call(messages, key)) return messages[key];
  if (CHROME_KEYS.has(String(key))) return chromeText(locale, key as ChromeKey);
  return surfaceText(locale, key as SurfaceKey);
}
