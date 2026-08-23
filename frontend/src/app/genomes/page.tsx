import type { Metadata } from "next";
import { SiteHeader } from "@/components/layout/SiteHeader";
import { SiteFooter } from "@/components/layout/SiteFooter";
import { Container, Section } from "@/components/ui";
import { GenomesOverview } from "@/components/genomes/GenomesOverview";

export const metadata: Metadata = {
  title: "Genomes",
  description:
    "Complete assembled genomes with assembly-level metadata from internationally recognised public databases.",
  alternates: { canonical: "/genomes" },
};

export default function GenomesPage() {
  return (
    <>
      <SiteHeader activeHref="/genomes" />
      <main id="main" className="pt-16">
        <Container width="wide">
          <Section
            eyebrow="Genomes · Complete assemblies"
            title="Genome sequence database"
            description="Complete assembled genomes with assembly-level metadata from internationally recognised public databases."
          >
            <GenomesOverview />
          </Section>
        </Container>
      </main>
      <SiteFooter />
    </>
  );
}
