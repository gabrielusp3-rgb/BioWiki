import type { Metadata } from "next";
import { SiteHeader } from "@/components/layout/SiteHeader";
import { SiteFooter } from "@/components/layout/SiteFooter";
import { Container, Section } from "@/components/ui";
import { PublicationsExplorer } from "@/components/publication/PublicationsExplorer";
import { PageIntro } from "@/components/i18n/PageIntro";

export const metadata: Metadata = {
  title: "Publications",
  description:
    "Browse real PubMed literature linked to sequences stored in BIOWIKI. Every record comes from the catalogue — no invented PMIDs.",
  alternates: { canonical: "/publications" },
};

export default function PublicationsPage() {
  return (
    <>
      <SiteHeader activeHref="/publications" />
      <main id="main" className="pt-16">
        <Container width="wide">
          <Section>
            <PageIntro eyebrow="pubEyebrow" title="pubTitle" description="pubDescription" />
            <PublicationsExplorer />
          </Section>
        </Container>
      </main>
      <SiteFooter />
    </>
  );
}
