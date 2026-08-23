import type { Metadata } from "next";
import { SiteHeader } from "@/components/layout/SiteHeader";
import { SiteFooter } from "@/components/layout/SiteFooter";
import { Container, Section } from "@/components/ui";
import { SequenceDetailContent } from "@/components/sequence/SequenceDetailContent";

interface PageProps {
  params: Promise<{ accession: string }>;
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { accession } = await params;
  const decoded = decodeURIComponent(accession);
  return {
    title: `${decoded} · Sequence`,
    description: `Full record for accession ${decoded}, including residues, annotations and linked publications.`,
    alternates: { canonical: `/sequences/${accession}` },
  };
}

export default async function SequenceDetailPage({ params }: PageProps) {
  const { accession } = await params;
  const decoded = decodeURIComponent(accession);

  return (
    <>
      <SiteHeader />
      <main id="main" className="pt-16">
        <Container width="wide">
          <Section
            eyebrow="Sequence record"
            title={decoded}
            description="Residues, metadata and bibliographic links as stored in the database — never fabricated."
          >
            <SequenceDetailContent accession={decoded} />
          </Section>
        </Container>
      </main>
      <SiteFooter />
    </>
  );
}
