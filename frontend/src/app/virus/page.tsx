import type { Metadata } from "next";
import { Suspense } from "react";
import { SiteHeader } from "@/components/layout/SiteHeader";
import { SiteFooter } from "@/components/layout/SiteFooter";
import { Container, Section } from "@/components/ui";
import { VirusStatistics } from "@/components/virus/VirusStatistics";
import { VirusExplorer } from "@/components/virus/VirusExplorer";

export const metadata: Metadata = {
  title: "Viruses",
  description:
    "Search, filter and explore real viral genomes and segments organised by family, host and genome type, with FASTA visualisation and multi-format downloads.",
  alternates: { canonical: "/virus" },
};

export default function VirusPage() {
  return (
    <>
      <SiteHeader activeHref="/virus" />
      <main id="main" className="pt-16">
        <Container width="wide">
          <Section
            eyebrow="Viruses · Viral sequences"
            title="Virus sequence database"
            description="Viral genomes and segments organised by family, host and Baltimore genome type, sourced from internationally recognised public databases — searchable, filterable and downloadable in FASTA, JSON and CSV."
          >
            <div className="flex flex-col gap-10">
              <VirusStatistics />
              <Suspense fallback={null}>
                <VirusExplorer />
              </Suspense>
            </div>
          </Section>
        </Container>
      </main>
      <SiteFooter />
    </>
  );
}
