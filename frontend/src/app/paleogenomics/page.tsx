import type { Metadata } from "next";
import { SiteHeader } from "@/components/layout/SiteHeader";
import { SiteFooter } from "@/components/layout/SiteFooter";
import { Container, Section } from "@/components/ui";
import { PaleogenomicsExplorer } from "@/components/paleogenomics/PaleogenomicsExplorer";
import { PageIntro } from "@/components/i18n/PageIntro";

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
          <Section>
            <PageIntro eyebrow="paleoPageEyebrow" title="paleoPageTitle" description="paleoPageDescription" />
            <PaleogenomicsExplorer />
          </Section>
        </Container>
      </main>
      <SiteFooter />
    </>
  );
}
