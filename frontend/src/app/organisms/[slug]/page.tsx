import type { Metadata } from "next";
import { SiteHeader } from "@/components/layout/SiteHeader";
import { SiteFooter } from "@/components/layout/SiteFooter";
import { Container, Section } from "@/components/ui";
import { OrganismDetailContent } from "@/components/organisms/OrganismDetailContent";

interface PageProps {
  params: Promise<{ slug: string }>;
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { slug } = await params;
  const decoded = decodeURIComponent(slug);
  return {
    title: `${decoded} · Organism`,
    description: `Taxonomy, sequence records, genome assemblies and publications for ${decoded}.`,
    alternates: { canonical: `/organisms/${slug}` },
  };
}

export default async function OrganismDetailPage({ params }: PageProps) {
  const { slug } = await params;
  const decoded = decodeURIComponent(slug);

  return (
    <>
      <SiteHeader activeHref="/organisms" />
      <main id="main" className="pt-16">
        <Container width="wide">
          <Section
            eyebrow="Organism"
            title={decoded.replace(/-/g, " ")}
            description="Real taxonomy and every record ingested for this organism — sequences, genome assemblies and linked publications."
          >
            <OrganismDetailContent identifier={decoded} />
          </Section>
        </Container>
      </main>
      <SiteFooter />
    </>
  );
}
