import type { Metadata } from "next";
import { SiteHeader } from "@/components/layout/SiteHeader";
import { SiteFooter } from "@/components/layout/SiteFooter";
import { Container, Section } from "@/components/ui";

export const metadata: Metadata = {
  title: "Documentation",
  description:
    "Getting started with BIOWIKI — browsing real sequences, programmatic access, integrity checks and exports.",
  alternates: { canonical: "/docs" },
};

const DOC_CARDS = [
  {
    eyebrow: "Browsing",
    accent: "#00F2FF",
    body: "Use the category pages (DNA, RNA, Proteins, CRISPR, Viruses, Genomes) to explore records, or the global search for accessions, gene names, organisms and publications. Every count shown is a live aggregate.",
  },
  {
    eyebrow: "Programmatic access",
    accent: "#39FF14",
    body: "The REST API is versioned under /api/v1. List endpoints use cursor pagination via nextCursor. See the in-app API page and the FastAPI OpenAPI UI at http://127.0.0.1:8000/docs when the backend is running.",
  },
  {
    eyebrow: "Data integrity",
    accent: "#7C5CFF",
    body: "The synchronisation status badge reflects whether cached counters match the live database. Integrity checks are exposed at /api/v1/statistics/integrity.",
  },
  {
    eyebrow: "Exports",
    accent: "#FFFF00",
    body: "Records can be downloaded as FASTA, GenBank, CSV or JSON from the Downloads page or directly from any detail view.",
  },
] as const;

export default function DocsPage() {
  return (
    <>
      <SiteHeader activeHref="/docs" />
      <main id="main" className="pt-16">
        <Container width="wide">
          <Section
            eyebrow="Documentation"
            title="Getting started"
            description="BIOWIKI stores only real biological sequences and their linked literature, sourced from recognised international databases."
          >
            <div className="grid gap-4 md:grid-cols-2">
              {DOC_CARDS.map((card) => (
                <div
                  key={card.eyebrow}
                  className="glass hairline relative overflow-hidden p-8"
                >
                  <span
                    className="absolute left-0 top-0 h-full w-[3px]"
                    style={{ background: card.accent }}
                  />
                  <p className="eyebrow mb-3">{card.eyebrow}</p>
                  <p className="text-sm leading-relaxed text-content-secondary">
                    {card.body}
                  </p>
                </div>
              ))}
            </div>
          </Section>
        </Container>
      </main>
      <SiteFooter />
    </>
  );
}
