import type { Metadata } from "next";
import { SiteHeader } from "@/components/layout/SiteHeader";
import { SiteFooter } from "@/components/layout/SiteFooter";
import { Container, Section } from "@/components/ui";
import { PublicationsExplorer } from "@/components/publication/PublicationsExplorer";

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
          <Section
            eyebrow="Literature · PubMed"
            title="Publication catalogue"
            description="Bibliographic records linked to stored sequences. Titles, authors, journals and PMIDs come from PubMed and source REFERENCE blocks — never synthesised."
          >
            <PublicationsExplorer />
          </Section>
        </Container>
      </main>
      <SiteFooter />
    </>
  );
}
