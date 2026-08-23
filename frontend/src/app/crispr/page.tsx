import type { Metadata } from "next";
import { Suspense } from "react";
import { SiteHeader } from "@/components/layout/SiteHeader";
import { SiteFooter } from "@/components/layout/SiteFooter";
import { Container, Section } from "@/components/ui";
import { CRISPRStatistics } from "@/components/crispr/CRISPRStatistics";
import { CRISPRExplorer } from "@/components/crispr/CRISPRExplorer";

export const metadata: Metadata = {
  title: "CRISPR Guides",
  description:
    "Search, filter and explore real CRISPR guide RNAs with PAM context, target genes, Cas systems and multi-format downloads.",
  alternates: { canonical: "/crispr" },
};

export default function CrisprPage() {
  return (
    <>
      <SiteHeader activeHref="/crispr" />
      <main id="main" className="pt-16">
        <Container width="wide">
          <Section
            eyebrow="CRISPR · Guide RNAs"
            title="CRISPR guide database"
            description="Guide RNAs with PAM context, target genes and Cas system annotations. Efficiency and specificity scores are served directly from source databases — never computed on the client."
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
