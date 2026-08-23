import type { Metadata } from "next";
import { SiteHeader } from "@/components/layout/SiteHeader";
import { SiteFooter } from "@/components/layout/SiteFooter";
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
          <Section
            eyebrow="About"
            title="A reference layer for real biology"
            description="BIOWIKI is an independent scientific database that unifies real biological sequences and their associated literature."
          >
            <div className="max-w-3xl space-y-6 text-sm leading-relaxed text-content-secondary">
              <p>
                Every record in BIOWIKI originates from a recognised international
                source — NCBI, UniProt, Ensembl, PDB, ENA and PubMed among them. There
                are no invented sequences, organisms, accession numbers or metadata.
              </p>
              <p>
                When a value is unknown or a collection is empty, the interface says so
                honestly rather than displaying an estimate. Counts, statistics and the
                scale of the database always reflect what is actually stored.
              </p>
              <p>
                Data is redistributed under the terms of the original providers; the
                BIOWIKI presentation layer is offered under CC BY 4.0.
              </p>
            </div>
          </Section>
        </Container>
      </main>
      <SiteFooter />
    </>
  );
}
