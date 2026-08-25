import Link from "next/link";
import { BrandLogo } from "@/components/brand/BrandLogo";
import { Container } from "@/components/ui";

interface FooterLink {
  label: string;
  href: string;
  external?: boolean;
}

interface FooterColumn {
  title: string;
  links: FooterLink[];
}

const COLUMNS: FooterColumn[] = [
  {
    title: "Database",
    links: [
      { label: "DNA", href: "/dna" },
      { label: "RNA", href: "/rna" },
      { label: "Proteins", href: "/proteins" },
      { label: "CRISPR", href: "/crispr" },
      { label: "Genomes", href: "/genomes" },
      { label: "Viruses", href: "/virus" },
      { label: "Publications", href: "/publications" },
    ],
  },
  {
    title: "Platform",
    links: [
      { label: "Search", href: "/search" },
      { label: "Organisms", href: "/organisms" },
      { label: "Downloads", href: "/downloads" },
      { label: "API", href: "/api" },
    ],
  },
  {
    title: "Resources",
    links: [
      { label: "Documentation", href: "/docs" },
      { label: "GitHub", href: "https://github.com/gabrielusp3-rgb/BioWiki", external: true },
      { label: "License", href: "/license" },
    ],
  },
];

const DATA_SOURCES = ["NCBI", "UniProt", "Ensembl", "PDB", "ENA", "PubMed"];

function FooterAnchor({ link }: { link: FooterLink }) {
  const className =
    "text-sm text-content-secondary transition-colors hover:text-content-primary";
  if (link.external) {
    return (
      <a href={link.href} target="_blank" rel="noopener noreferrer" className={className}>
        {link.label}
      </a>
    );
  }
  return (
    <Link href={link.href} className={className}>
      {link.label}
    </Link>
  );
}

export function SiteFooter() {
  const year = new Date().getFullYear();

  return (
    <footer className="relative mt-24 border-t border-glass-divider bg-bg-secondary/60 backdrop-blur-glass">
      <Container width="wide">
        <div className="grid grid-cols-2 gap-10 py-16 sm:grid-cols-3 lg:grid-cols-5">
          {/* Brand */}
          <div className="col-span-2 flex flex-col gap-4">
            <Link href="/" className="inline-flex items-center">
              <BrandLogo />
            </Link>
            <p className="max-w-sm text-sm leading-relaxed text-content-secondary">
              A local catalogue of real molecular sequences aggregated from
              public sequence archives.
            </p>
            <div className="mt-2 flex flex-col gap-2">
              <span className="eyebrow">Data sources</span>
              <div className="flex flex-wrap gap-2">
                {DATA_SOURCES.map((source) => (
                  <span
                    key={source}
                    className="border border-glass-border px-2.5 py-1 font-mono text-[11px] text-content-secondary"
                  >
                    {source}
                  </span>
                ))}
              </div>
            </div>
          </div>

          {/* Link columns */}
          {COLUMNS.map((column) => (
            <div key={column.title} className="flex flex-col gap-4">
              <span className="eyebrow">{column.title}</span>
              <nav className="flex flex-col gap-3">
                {column.links.map((link) => (
                  <FooterAnchor key={link.label} link={link} />
                ))}
              </nav>
            </div>
          ))}
        </div>

        {/* Bottom bar */}
        <div className="flex flex-col items-start justify-between gap-4 border-t border-glass-divider py-6 sm:flex-row sm:items-center">
          <p className="text-xs text-content-muted">
            © {year} BIOWIKI. Sequence data remains subject to the licenses of its
            respective source databases.
          </p>
          <div className="flex items-center gap-5">
            <Link href="/license" className="text-xs text-content-muted transition-colors hover:text-content-primary">
              License
            </Link>
            <Link href="/docs" className="text-xs text-content-muted transition-colors hover:text-content-primary">
              Documentation
            </Link>
            <a
              href="https://github.com/gabrielusp3-rgb/BioWiki"
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-content-muted transition-colors hover:text-content-primary"
            >
              GitHub
            </a>
          </div>
        </div>
      </Container>
    </footer>
  );
}
