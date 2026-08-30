import type { Metadata } from "next";
import { SiteHeader } from "@/components/layout/SiteHeader";
import { SiteFooter } from "@/components/layout/SiteFooter";
import { Container, Section } from "@/components/ui";
import { PaleogenomicsExplorer } from "@/components/paleogenomics/PaleogenomicsExplorer";

export const metadata: Metadata = {
  title: "Paleogenomics",
  description:
    "Curated extinct species, ancient DNA, archaic hominins and introgression in living humans — authentic records inside BioWiki.",
  alternates: { canonical: "/paleogenomics" },
};

export default function PaleogenomicsPage() {
  return (
    <>
      <SiteHeader activeHref="/paleogenomics" />
      <main id="main" className="pt-16">
        <Container width="wide">
          <Section
            eyebrow="Paleogenomics · Extinct species · Archaic hominins"
            title="Paleogenomics"
            description="A curated collection of authentic ancient DNA, extinct-organism records, archaic hominins, and separately modelled introgression in living humans. Not a second catalogue. Unknown is preferred to invention."
          >
            <PaleogenomicsExplorer />
          </Section>
        </Container>
      </main>
      <SiteFooter />
    </>
  );
}
