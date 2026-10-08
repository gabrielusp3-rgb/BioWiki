import type { Metadata } from "next";
import { SiteHeader } from "@/components/layout/SiteHeader";
import { SiteFooter } from "@/components/layout/SiteFooter";
import { Container, Section } from "@/components/ui";
import { DownloadsSection } from "@/components/sections/DownloadsSection";
import { PageIntro } from "@/components/i18n/PageIntro";

export const metadata: Metadata = {
  title: "Downloads",
  description:
    "Export real BIOWIKI records in FASTA, JSON and CSV. Files are generated from stored sequences.",
  alternates: { canonical: "/downloads" },
};

export default function DownloadsPage() {
  return (
    <>
      <SiteHeader activeHref="/downloads" />
      <main id="main" className="pt-16">
        <Container width="wide">
          <Section>
            <PageIntro eyebrow="dlEyebrow" title="dlTitle" description="dlDescription" />
            <DownloadsSection />
          </Section>
        </Container>
      </main>
      <SiteFooter />
    </>
  );
}
