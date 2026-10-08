import type { Metadata } from "next";
import { SiteHeader } from "@/components/layout/SiteHeader";
import { SiteFooter } from "@/components/layout/SiteFooter";
import { LicenseCopy } from "@/components/i18n/StaticPages";
import { Container, Section } from "@/components/ui";

export const metadata: Metadata = {
  title: "License & Data Sources",
  description:
    "BIOWIKI aggregates sequence data from internationally recognised public databases. Each source retains its own license and usage terms.",
  alternates: { canonical: "/license" },
};

export default function LicensePage() {
  return (
    <>
      <SiteHeader activeHref="/license" />
      <main id="main" className="pt-16">
        <Container width="default">
          <Section>
            <LicenseCopy />
          </Section>
        </Container>
      </main>
      <SiteFooter />
    </>
  );
}
