import type { Metadata } from "next";
import { SiteHeader } from "@/components/layout/SiteHeader";
import { SiteFooter } from "@/components/layout/SiteFooter";
import { Container, Section } from "@/components/ui";
import { DownloadsSection } from "@/components/sections/DownloadsSection";

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
          <Section
            eyebrow="Bulk data"
            title="Downloads"
            description="Export real records in standard formats. Files are generated on demand from the live database."
          >
            <DownloadsSection />
          </Section>
        </Container>
      </main>
      <SiteFooter />
    </>
  );
}
