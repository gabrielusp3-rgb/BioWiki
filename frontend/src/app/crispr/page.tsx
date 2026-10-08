import type { Metadata } from "next";
import { Suspense } from "react";
import { SiteHeader } from "@/components/layout/SiteHeader";
import { SiteFooter } from "@/components/layout/SiteFooter";
import { Container, Section } from "@/components/ui";
import { CRISPRStatistics } from "@/components/crispr/CRISPRStatistics";
import { CRISPRExplorer } from "@/components/crispr/CRISPRExplorer";
import { PageIntro } from "@/components/i18n/PageIntro";

export const metadata: Metadata = {
  title: "CRISPR",
  description:
    "Natural CRISPR-Cas elements, experimentally reported guides, and computational Cas9 targets, each labeled by evidence type. Scores are never invented on the client.",
  alternates: { canonical: "/crispr" },
};

export default function CrisprPage() {
  return (
    <>
      <SiteHeader activeHref="/crispr" />
      <main id="main" className="pt-16">
        <Container width="wide">
          <Section>
            <PageIntro eyebrow="crisprEyebrow" title="crisprTitle" description="crisprDescription" />
            <div className="flex flex-col gap-10">
              <CRISPRStatistics />
              <Suspense fallback={null}>
                <CRISPRExplorer />
              </Suspense>
            </div>
          </Section>
        </Container>
      </main>
      <SiteFooter />
    </>
  );
}
