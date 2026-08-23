import type { Metadata } from "next";
import { Suspense } from "react";
import { SiteHeader } from "@/components/layout/SiteHeader";
import { SiteFooter } from "@/components/layout/SiteFooter";
import { Container, Section } from "@/components/ui";
import { ProteinStatistics } from "@/components/protein/ProteinStatistics";
import { ProteinExplorer } from "@/components/protein/ProteinExplorer";

export const metadata: Metadata = {
  title: "Proteins",
  description:
    "Search, filter and explore real protein sequences with functional annotations, 3D structure links, residue colouring and multi-format downloads.",
  alternates: { canonical: "/proteins" },
};

export default function ProteinsPage() {
  return (
    <>
      <SiteHeader activeHref="/proteins" />
      <main id="main" className="pt-16">
        <Container width="wide">
          <Section
            eyebrow="Proteins · Amino acid sequences"
            title="Protein sequence database"
            description="Amino acid sequences with functional annotations, domains and 3D structure references from UniProt, RefSeq and the Protein Data Bank — searchable, filterable and downloadable in FASTA, JSON and CSV."
          >
            <div className="flex flex-col gap-10">
              <ProteinStatistics />
              <Suspense fallback={null}>
                <ProteinExplorer />
              </Suspense>
            </div>
          </Section>
        </Container>
      </main>
      <SiteFooter />
    </>
  );
}
