"use client";

import { PageIntro } from "@/components/i18n/PageIntro";
import { ExternalIcon } from "@/components/ui/Icons";
import { useLocale } from "@/lib/i18n/LocaleProvider";
import type { ChromeKey } from "@/lib/i18n/chrome";

export function AboutCopy() {
  const { t } = useLocale();
  return (
    <>
      <PageIntro eyebrow="aboutEyebrow" title="aboutTitle" description="aboutLead" />
      <div className="max-w-3xl space-y-6 text-sm leading-relaxed text-content-secondary">
        <p>{t("aboutP1")}</p>
        <p>{t("aboutP2")}</p>
        <p>{t("aboutP3")}</p>
      </div>
    </>
  );
}

const CONNECTORS: { name: string; key: ChromeKey; url: string }[] = [
  { name: "NCBI", key: "srcNcbi", url: "https://www.ncbi.nlm.nih.gov/" },
  { name: "UniProt", key: "srcUniprot", url: "https://www.uniprot.org/" },
  { name: "Ensembl", key: "srcEnsembl", url: "https://www.ensembl.org/" },
  { name: "PDB", key: "srcPdb", url: "https://www.rcsb.org/" },
  { name: "ENA", key: "srcEna", url: "https://www.ebi.ac.uk/ena/browser/home" },
  { name: "Rfam", key: "srcRfam", url: "https://rfam.org/" },
];

export function LicenseCopy() {
  const { t } = useLocale();
  return (
    <>
      <PageIntro eyebrow="licenseEyebrow" title="licenseTitle" description="licenseLead" />
      <p className="mb-4 font-display text-xs font-bold uppercase tracking-widest text-content-muted">
        {t("licenseConnectors")}
      </p>
      <div className="flex flex-col gap-4">
        {CONNECTORS.map((source) => (
          <a
            key={source.name}
            href={source.url}
            target="_blank"
            rel="noopener noreferrer"
            className="glass hairline group flex items-center justify-between gap-4 p-5 transition-colors duration-300 hover:border-white/20"
          >
            <div className="flex flex-col gap-1">
              <span className="font-display text-sm font-bold uppercase tracking-wide text-content-primary">
                {source.name}
              </span>
              <span className="text-sm text-content-secondary">{t(source.key)}</span>
            </div>
            <ExternalIcon className="h-4 w-4 shrink-0 text-content-muted transition-colors group-hover:text-content-primary" />
          </a>
        ))}
      </div>
      <p className="mb-4 mt-10 font-display text-xs font-bold uppercase tracking-widest text-content-muted">
        {t("licenseRelated")}
      </p>
      <a
        href="https://www.ddbj.nig.ac.jp/"
        target="_blank"
        rel="noopener noreferrer"
        className="glass hairline flex items-center justify-between gap-4 p-5"
      >
        <div className="flex flex-col gap-1">
          <span className="font-display text-sm font-bold uppercase tracking-wide text-content-primary">DDBJ</span>
          <span className="text-sm text-content-secondary">{t("srcDdbj")}</span>
        </div>
        <ExternalIcon className="h-4 w-4 shrink-0 text-content-muted" />
      </a>
    </>
  );
}

const DOCS: { eyebrow: ChromeKey; body: ChromeKey; accent: string }[] = [
  { eyebrow: "docsBrowse", body: "docsBrowseBody", accent: "#00F2FF" },
  { eyebrow: "docsApi", body: "docsApiBody", accent: "#39FF14" },
  { eyebrow: "docsIntegrity", body: "docsIntegrityBody", accent: "#7C5CFF" },
  { eyebrow: "docsExport", body: "docsExportBody", accent: "#FFFF00" },
];

export function DocsCopy() {
  const { t } = useLocale();
  return (
    <>
      <PageIntro eyebrow="docsEyebrow" title="docsTitle" description="docsLead" />
      <div className="grid gap-4 md:grid-cols-2">
        {DOCS.map((card) => (
          <div key={card.eyebrow} className="glass hairline relative overflow-hidden p-8">
            <span className="absolute left-0 top-0 h-full w-[3px]" style={{ background: card.accent }} />
            <p className="eyebrow mb-3">{t(card.eyebrow)}</p>
            <p className="text-sm leading-relaxed text-content-secondary">{t(card.body)}</p>
          </div>
        ))}
      </div>
    </>
  );
}
