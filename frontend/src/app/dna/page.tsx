import type { Metadata } from "next";
import { Suspense } from "react";
import { SiteHeader } from "@/components/layout/SiteHeader";
import { SiteFooter } from "@/components/layout/SiteFooter";
import { Container, Section } from "@/components/ui";
import { DNAStats } from "@/components/dna/DNAStats";
import { DNAExplorer } from "@/components/dna/DNAExplorer";

export const metadata: Metadata = {
  title: "DNA Sequences",
  description:
    "Search, filter and explore real DNA sequences with FASTA visualisation, base-pair colouring and multi-format downloads.",
  alternates: { canonical: "/dna" },
};

export default function DnaPage() {
  return (
    <>
      <SiteHeader activeHref="/dna" />
      <main id="main" className="pt-16">
        <Container width="wide">
          <Section
            eyebrow="DNA · Deoxyribonucleic acid"
            title="DNA sequence database"
            description="Genomic, coding and regulatory nucleotide sequences from internationally recognised public databases — searchable, filterable and downloadable in FASTA, JSON and CSV."
          >
            <div className="flex flex-col gap-10">
              <DNAStats />
              <Suspense fallback={null}>
                <DNAExplorer />
              </Suspense>
            </div>
          </Section>
        </Container>
      </main>
      <SiteFooter />
    </>
  );
}
