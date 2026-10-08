import type { Metadata } from "next";
import { SiteHeader } from "@/components/layout/SiteHeader";
import { SiteFooter } from "@/components/layout/SiteFooter";
import { Container, Section } from "@/components/ui";
import { GenomesOverview } from "@/components/genomes/GenomesOverview";
import { PageIntro } from "@/components/i18n/PageIntro";

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
          <Section>
            <PageIntro eyebrow="genomeEyebrow" title="genomeTitle" description="genomeDescription" />
            <GenomesOverview />
          </Section>
        </Container>
      </main>
      <SiteFooter />
    </>
  );
}
