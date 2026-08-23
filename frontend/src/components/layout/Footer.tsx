import Link from "next/link";
import { Container } from "@/components/ui/Container";

export function Footer() {
  return (
    <footer className="border-t border-white/5 py-16">
      <Container>
        <div className="grid gap-10 md:grid-cols-4">
          <div>
            <p className="display text-lg text-white">
              BIO<span className="text-dna">WIKI</span>
            </p>
            <p className="mt-3 max-w-xs text-xs leading-relaxed text-neutral-500">
              Universal biological sequence database. Real records sourced from
              recognised international databases.
            </p>
          </div>
          <FooterCol
            title="Data"
            links={[
              ["DNA", "/dna"],
              ["RNA", "/rna"],
              ["Proteins", "/proteins"],
              ["Genomes", "/genomes"],
            ]}
          />
          <FooterCol
            title="Platform"
            links={[
              ["Search", "/search"],
              ["API", "/api"],
              ["Downloads", "/downloads"],
              ["Documentation", "/docs"],
            ]}
          />
          <FooterCol
            title="Sources"
            links={[
              ["NCBI", "https://www.ncbi.nlm.nih.gov/"],
              ["UniProt", "https://www.uniprot.org/"],
              ["Ensembl", "https://www.ensembl.org/"],
              ["PDB", "https://www.rcsb.org/"],
            ]}
          />
        </div>
        <div className="mt-12 flex flex-col gap-3 border-t border-white/5 pt-6 text-[0.7rem] uppercase tracking-widest text-neutral-600 md:flex-row md:justify-between">
          <span>© {new Date().getFullYear()} BIOWIKI</span>
          <span>Data under CC BY 4.0 — from original providers</span>
        </div>
      </Container>
    </footer>
  );
}

function FooterCol({
  title,
  links,
}: {
  title: string;
  links: [string, string][];
}) {
  return (
    <div>
      <p className="eyebrow mb-4">{title}</p>
      <ul className="space-y-2">
        {links.map(([label, href]) => (
          <li key={label}>
            <Link
              href={href}
              className="text-xs text-neutral-400 transition-colors hover:text-white"
            >
              {label}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
