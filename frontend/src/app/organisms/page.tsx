import type { Metadata } from "next";
import { SiteHeader } from "@/components/layout/SiteHeader";
import { SiteFooter } from "@/components/layout/SiteFooter";
import { Container, Section } from "@/components/ui";
import { OrganismsExplorer } from "@/components/organisms/OrganismsExplorer";

export const metadata: Metadata = {
  title: "Organisms",
  description:
    "Reference organisms with verified NCBI Taxonomy identifiers, lineage and live sequence counts from the BIOWIKI database.",
  alternates: { canonical: "/organisms" },
};

export default function OrganismsPage() {
  return (
    <>
      <SiteHeader activeHref="/organisms" />
      <main id="main" className="pt-16">
        <Container width="wide">
          <Section
            eyebrow="Taxonomy · NCBI"
            title="Organism catalogue"
            description="Every organism is identified by a real NCBI Taxonomy ID. Sequence counts are live aggregates from stored records — never estimates."
          >
            <OrganismsExplorer />
          </Section>
        </Container>
      </main>
      <SiteFooter />
    </>
  );
}
