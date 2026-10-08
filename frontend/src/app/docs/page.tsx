import type { Metadata } from "next";
import { SiteHeader } from "@/components/layout/SiteHeader";
import { SiteFooter } from "@/components/layout/SiteFooter";
import { DocsCopy } from "@/components/i18n/StaticPages";
import { Container, Section } from "@/components/ui";

export const metadata: Metadata = {
  title: "Documentation",
  description:
    "Getting started with BIOWIKI — browsing real sequences, programmatic access, integrity checks and exports.",
  alternates: { canonical: "/docs" },
};

export default function DocsPage() {
  return (
    <>
      <SiteHeader activeHref="/docs" />
      <main id="main" className="pt-16">
        <Container width="wide">
          <Section>
            <DocsCopy />
          </Section>
        </Container>
      </main>
      <SiteFooter />
    </>
  );
}
