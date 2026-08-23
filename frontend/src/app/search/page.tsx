import type { Metadata } from "next";
import { Suspense } from "react";
import { SiteHeader } from "@/components/layout/SiteHeader";
import { SiteFooter } from "@/components/layout/SiteFooter";
import { Container, Section } from "@/components/ui";
import { SearchPageContent } from "@/components/search/SearchPageContent";

export const metadata: Metadata = {
  title: "Search",
  description:
    "Search real biological sequences, genes, organisms, accessions and PubMed publications stored in BIOWIKI.",
  alternates: { canonical: "/search" },
};

export default function SearchPage() {
  return (
    <>
      <SiteHeader activeHref="/search" />
      <main id="main" className="pt-16">
        <Container width="wide">
          <Section
            eyebrow="Global search"
            title="Search the database"
            description="Query accessions, gene names, organisms, taxonomy IDs and publications. Results come from stored records only."
          >
            <Suspense fallback={null}>
              <SearchPageContent />
            </Suspense>
          </Section>
        </Container>
      </main>
      <SiteFooter />
    </>
  );
}
