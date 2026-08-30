import type { ComponentType, SVGProps } from "react";
import {
  CrisprIcon,
  DnaIcon,
  GenomeIcon,
  ProteinIcon,
  RnaIcon,
  VirusIcon,
} from "@/components/ui/Icons";
import type { CategoryKey } from "@/lib/design-tokens";

export interface CategoryCardData {
  key: CategoryKey;
  label: string;
  description: string;
  href: string;
  Icon: ComponentType<SVGProps<SVGSVGElement>>;
}

/** Category entry points. Record counts come only from the live `/statistics` API. */
export const CATEGORY_CARDS: CategoryCardData[] = [
  {
    key: "dna",
    label: "DNA",
    description: "Genomic and coding nucleotide sequences across the tree of life.",
    href: "/dna",
    Icon: DnaIcon,
  },
  {
    key: "rna",
    label: "RNA",
    description: "Transcripts spanning mRNA, tRNA, rRNA and regulatory RNA classes.",
    href: "/rna",
    Icon: RnaIcon,
  },
  {
    key: "protein",
    label: "Proteins",
    description: "Amino acid sequences with functional and structural annotations.",
    href: "/proteins",
    Icon: ProteinIcon,
  },
  {
    key: "virus",
    label: "Viruses",
    description: "Viral genomes and segments organised by family and host.",
    href: "/virus",
    Icon: VirusIcon,
  },
  {
    key: "crispr",
    label: "CRISPR",
    description: "Natural CRISPR-Cas, experimental guides, and computational targets, labeled separately.",
    href: "/crispr",
    Icon: CrisprIcon,
  },
  {
    key: "genome",
    label: "Genomes",
    description: "Complete assembled genomes with assembly-level metadata.",
    href: "/genomes",
    Icon: GenomeIcon,
  },
];
