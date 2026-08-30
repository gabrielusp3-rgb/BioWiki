import type { Metadata } from "next";
import { SiteHeader } from "@/components/layout/SiteHeader";
import { SiteFooter } from "@/components/layout/SiteFooter";
import { Container, Section } from "@/components/ui";
import { IntrogressionExplorer } from "@/components/paleogenomics/IntrogressionExplorer";

export const metadata: Metadata = {
  title: "Archaic introgression · Paleogenomics",
  description:
    "Gene-level Neanderthal and Denisovan ancestry in living Homo sapiens — not DNA extracted from archaic specimens.",
  alternates: { canonical: "/paleogenomics/introgression" },
};

export default function PaleogenomicsIntrogressionPage() {
  return (
    <>
      <SiteHeader activeHref="/paleogenomics" />
      <main id="main" className="pt-16">
        <Container width="wide">
          <Section
            eyebrow="Paleogenomics · Living Homo sapiens"
            title="Archaic introgression in living humans"
            description="These loci are genomic segments in present-day humans with published evidence of Neanderthal or Denisovan ancestry. They are not samples taken from an archaic bone."
          >
            <IntrogressionExplorer />
          </Section>
        </Container>
      </main>
      <SiteFooter />
    </>
  );
}
