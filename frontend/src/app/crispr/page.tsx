import type { Metadata } from "next";
import { Suspense } from "react";
import { SiteHeader } from "@/components/layout/SiteHeader";
import { SiteFooter } from "@/components/layout/SiteFooter";
import { Container, Section } from "@/components/ui";
import { CRISPRStatistics } from "@/components/crispr/CRISPRStatistics";
import { CRISPRExplorer } from "@/components/crispr/CRISPRExplorer";

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
          <Section
            eyebrow="CRISPR · evidence types"
            title="CRISPR catalogue"
            description="Natural CRISPR-Cas elements, experimental guides, and computational / predicted Cas9 NGG sites. Computational records are never labeled experimental. Efficiency scores come from sources or stay empty — they are not invented here."
          >
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
