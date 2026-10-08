import type { Metadata } from "next";
import { SiteHeader } from "@/components/layout/SiteHeader";
import { SiteFooter } from "@/components/layout/SiteFooter";
import { AboutCopy } from "@/components/i18n/StaticPages";
import { Container, Section } from "@/components/ui";

export const metadata: Metadata = {
  title: "About",
  description:
    "BIOWIKI is an independent scientific database that unifies real biological sequences and their associated literature.",
  alternates: { canonical: "/about" },
};

export default function AboutPage() {
  return (
    <>
      <SiteHeader activeHref="/about" />
      <main id="main" className="pt-16">
        <Container width="default">
          <Section>
            <AboutCopy />
          </Section>
        </Container>
      </main>
      <SiteFooter />
    </>
  );
}
