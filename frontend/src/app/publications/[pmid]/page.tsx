import type { Metadata } from "next";
import { SiteHeader } from "@/components/layout/SiteHeader";
import { SiteFooter } from "@/components/layout/SiteFooter";
import { Container, Section } from "@/components/ui";
import { PublicationDetailContent } from "@/components/publication/PublicationDetailContent";

interface PageProps {
  params: Promise<{ pmid: string }>;
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { pmid } = await params;
  return {
    title: `PMID ${pmid} · Publication`,
    description: `Bibliographic record for PubMed ID ${pmid} with linked sequence records.`,
    alternates: { canonical: `/publications/${pmid}` },
  };
}

export default async function PublicationPage({ params }: PageProps) {
  const { pmid } = await params;

  return (
    <>
      <SiteHeader activeHref="/publications" />
      <main id="main" className="pt-16">
        <Container width="wide">
          <Section
            eyebrow="Publication"
            title={`PMID ${pmid}`}
            description="Bibliographic record from PubMed — title, authors, journal, abstract and the sequence records that cite it."
          >
            <PublicationDetailContent pubmedId={pmid} />
          </Section>
        </Container>
      </main>
      <SiteFooter />
    </>
  );
}
