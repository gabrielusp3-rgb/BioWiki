import type { Metadata } from "next";
import { SiteHeader } from "@/components/layout/SiteHeader";
import { SiteFooter } from "@/components/layout/SiteFooter";
import { Container, Section } from "@/components/ui";
import { ExternalIcon } from "@/components/ui/Icons";

export const metadata: Metadata = {
  title: "License & Data Sources",
  description:
    "BIOWIKI aggregates sequence data from internationally recognised public databases. Each source retains its own license and usage terms.",
  alternates: { canonical: "/license" },
};

interface DataSource {
  name: string;
  description: string;
  url: string;
}

const DATA_SOURCES: DataSource[] = [
  {
    name: "NCBI",
    description: "GenBank and RefSeq nucleotide and protein records, taxonomy.",
    url: "https://www.ncbi.nlm.nih.gov/",
  },
  {
    name: "UniProt",
    description: "Reviewed and unreviewed protein sequence and functional annotation.",
    url: "https://www.uniprot.org/",
  },
  {
    name: "Ensembl",
    description: "Genome annotation and comparative genomics.",
    url: "https://www.ensembl.org/",
  },
  {
    name: "PDB",
    description: "Experimentally determined 3D protein and nucleic acid structures.",
    url: "https://www.rcsb.org/",
  },
  {
    name: "ENA",
    description: "European Nucleotide Archive — raw and assembled sequence data.",
    url: "https://www.ebi.ac.uk/ena/browser/home",
  },
  {
    name: "DDBJ",
    description: "DNA Data Bank of Japan — nucleotide sequence submissions.",
    url: "https://www.ddbj.nig.ac.jp/",
  },
];

export default function LicensePage() {
  return (
    <>
      <SiteHeader activeHref="/license" />
      <main id="main" className="pt-16">
        <Container width="default">
          <Section
            eyebrow="License & Attribution"
            title="Data sources and usage terms"
            description="BIOWIKI does not claim ownership of the biological records it indexes. Each sequence remains subject to the license and usage terms of its originating database."
          >
            <div className="flex flex-col gap-4">
              {DATA_SOURCES.map((source) => (
                <a
                  key={source.name}
                  href={source.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="glass hairline group flex items-center justify-between gap-4 p-5 transition-colors duration-300 hover:border-white/20"
                >
                  <div className="flex flex-col gap-1">
                    <span className="font-display text-sm font-bold uppercase tracking-wide text-content-primary">
                      {source.name}
                    </span>
                    <span className="text-sm text-content-secondary">{source.description}</span>
                  </div>
                  <ExternalIcon className="h-4 w-4 shrink-0 text-content-muted transition-colors group-hover:text-content-primary" />
                </a>
              ))}
            </div>

            <p className="mt-10 max-w-2xl text-sm leading-relaxed text-content-secondary">
              BIOWIKI never fabricates sequences, organisms, accessions or metadata. Every record
              displayed once the database is connected is traceable to one of the sources above,
              along with its original accession. Consult each source directly for the specific
              license terms that apply to your intended use.
            </p>
          </Section>
        </Container>
      </main>
      <SiteFooter />
    </>
  );
}
