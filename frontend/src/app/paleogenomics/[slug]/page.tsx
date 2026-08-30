import type { Metadata } from "next";
import { SiteHeader } from "@/components/layout/SiteHeader";
import { SiteFooter } from "@/components/layout/SiteFooter";
import { Container, Section } from "@/components/ui";
import { PaleogenomicsProfileContent } from "@/components/paleogenomics/PaleogenomicsProfileContent";

interface PageProps {
  params: Promise<{ slug: string }>;
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { slug } = await params;
  const decoded = decodeURIComponent(slug);
  return {
    title: `${decoded.replace(/-/g, " ")} · Paleogenomics`,
    description: `Source-backed palaeogenomic profile for ${decoded.replace(/-/g, " ")}.`,
    alternates: { canonical: `/paleogenomics/${slug}` },
  };
}

export default async function PaleogenomicsSpeciesPage({ params }: PageProps) {
  const { slug } = await params;
  const decoded = decodeURIComponent(slug);

  return (
    <>
      <SiteHeader activeHref="/paleogenomics" />
      <main id="main" className="pt-16">
        <Container width="wide">
          <Section
            eyebrow="Paleogenomics"
            description="Deterministic, reviewed scientific content. Ancient specimen DNA is not introgression in living humans."
          >
            <PaleogenomicsProfileContent slug={decoded} />
          </Section>
        </Container>
      </main>
      <SiteFooter />
    </>
  );
}
