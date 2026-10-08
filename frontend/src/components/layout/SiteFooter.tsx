"use client";

import Link from "next/link";
import { useLocale } from "@/lib/i18n/LocaleProvider";
import { BrandLogo } from "@/components/brand/BrandLogo";
import { Container } from "@/components/ui";

const DATA_SOURCES = ["NCBI", "UniProt", "Ensembl", "PDB", "ENA", "PubMed"];

export function SiteFooter() {
  const year = new Date().getFullYear();
  const { t } = useLocale();
  const columns = [
    {
      title: t("footerDatabase"),
      links: [
        { label: t("navDna"), href: "/dna" },
        { label: t("navRna"), href: "/rna" },
        { label: t("navProteins"), href: "/proteins" },
        { label: t("navCrispr"), href: "/crispr" },
        { label: t("navGenomes"), href: "/genomes" },
        { label: t("navVirus"), href: "/virus" },
        { label: t("navPaleogenomics"), href: "/paleogenomics" },
        { label: t("navPublications"), href: "/publications" },
      ],
    },
    {
      title: t("footerPlatform"),
      links: [
        { label: t("actionSearch"), href: "/search" },
        { label: t("navOrganisms"), href: "/organisms" },
        { label: t("navDownloads"), href: "/downloads" },
      ],
    },
    {
      title: t("footerResources"),
      links: [
        { label: t("footerDocs"), href: "/docs" },
        { label: "GitHub", href: "https://github.com/gabrielusp3-rgb/BioWiki", external: true },
        { label: t("footerLicense"), href: "/license" },
      ],
    },
  ];

  return (
    <footer className="relative mt-24 border-t border-glass-divider bg-bg-secondary/60 backdrop-blur-glass">
      <Container width="wide">
        <div className="grid grid-cols-2 gap-10 py-16 sm:grid-cols-3 lg:grid-cols-5">
          {/* Brand */}
          <div className="col-span-2 flex flex-col gap-4">
            <Link href="/" className="inline-flex items-center">
              <BrandLogo />
            </Link>
            <p className="max-w-sm text-sm leading-relaxed text-content-secondary">{t("footerBlurb")}</p>
            <div className="mt-2 flex flex-col gap-2">
              <span className="eyebrow">{t("footerSources")}</span>
              <div className="flex flex-wrap gap-2">
                {DATA_SOURCES.map((source) => (
                  <span
                    key={source}
                    className="border border-glass-border px-2.5 py-1 font-mono text-[11px] text-content-secondary"
                  >
                    {source}
                  </span>
                ))}
              </div>
            </div>
          </div>

          {/* Link columns */}
          {columns.map((column) => (
            <div key={column.title} className="flex flex-col gap-4">
              <span className="eyebrow">{column.title}</span>
              <nav className="flex flex-col gap-3">
                {column.links.map((link) =>
                  link.external ? (
                    <a key={link.href} href={link.href} target="_blank" rel="noopener noreferrer" className="text-sm text-content-secondary transition-colors hover:text-content-primary">
                      {link.label}
                    </a>
                  ) : (
                    <Link key={link.href} href={link.href} className="text-sm text-content-secondary transition-colors hover:text-content-primary">
                      {link.label}
                    </Link>
                  ),
                )}
              </nav>
            </div>
          ))}
        </div>

        {/* Bottom bar */}
        <div className="flex flex-col items-start justify-between gap-4 border-t border-glass-divider py-6 sm:flex-row sm:items-center">
          <p className="text-xs text-content-muted">
            © {year} BIOWIKI. {t("footerRights")}
          </p>
          <div className="flex items-center gap-5">
            <Link href="/license" className="text-xs text-content-muted transition-colors hover:text-content-primary">
              {t("footerLicense")}
            </Link>
            <Link href="/docs" className="text-xs text-content-muted transition-colors hover:text-content-primary">
              {t("footerDocs")}
            </Link>
            <a
              href="https://github.com/gabrielusp3-rgb/BioWiki"
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-content-muted transition-colors hover:text-content-primary"
            >
              GitHub
            </a>
          </div>
        </div>
      </Container>
    </footer>
  );
}
