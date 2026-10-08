import type { Metadata } from "next";
import { Suspense } from "react";
import { SiteHeader } from "@/components/layout/SiteHeader";
import { SiteFooter } from "@/components/layout/SiteFooter";
import { Container, Section } from "@/components/ui";
import { RNAStats } from "@/components/rna/RNAStats";
import { RNAExplorer } from "@/components/rna/RNAExplorer";
import { PageIntro } from "@/components/i18n/PageIntro";

export const metadata: Metadata = {
  title: "RNA Sequences",
  description:
    "Search, filter and explore real RNA sequences — mRNA, tRNA, rRNA, lncRNA, miRNA and snRNA — with FASTA visualisation, base colouring and multi-format downloads.",
  alternates: { canonical: "/rna" },
};

export default function RnaPage() {
  return (
    <>
      <SiteHeader activeHref="/rna" />
      <main id="main" className="pt-16">
        <Container width="wide">
          <Section>
            <PageIntro eyebrow="rnaEyebrow" title="rnaTitle" description="rnaDescription" />
            <div className="flex flex-col gap-10">
              <RNAStats />
              <Suspense fallback={null}>
                <RNAExplorer />
              </Suspense>
            </div>
          </Section>
        </Container>
      </main>
      <SiteFooter />
    </>
  );
}
