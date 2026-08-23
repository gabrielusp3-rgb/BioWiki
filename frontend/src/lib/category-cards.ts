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
  /** Institutional interface count — replace with real backend totals later. */
  count: number;
  href: string;
  Icon: ComponentType<SVGProps<SVGSVGElement>>;
}

/**
 * INSTITUTIONAL CATEGORY FIGURES — interface only.
 * Counts mirror the scale targets from the platform brief and are isolated here
 * so they can be replaced by real `/statistics/by-category` values. No records
 * are fabricated.
 */
export const CATEGORY_CARDS: CategoryCardData[] = [
  {
    key: "dna",
    label: "DNA",
    description: "Genomic and coding nucleotide sequences across the tree of life.",
    count: 500_000,
    href: "/dna",
    Icon: DnaIcon,
  },
  {
    key: "rna",
    label: "RNA",
    description: "Transcripts spanning mRNA, tRNA, rRNA and regulatory RNA classes.",
    count: 400_000,
    href: "/rna",
    Icon: RnaIcon,
  },
  {
    key: "protein",
    label: "Proteins",
    description: "Amino acid sequences with functional and structural annotations.",
    count: 500_000,
    href: "/proteins",
    Icon: ProteinIcon,
  },
  {
    key: "virus",
    label: "Viruses",
    description: "Viral genomes and segments organised by family and host.",
    count: 120_000,
    href: "/virus",
    Icon: VirusIcon,
  },
  {
    key: "crispr",
    label: "CRISPR",
    description: "Guide RNAs with PAM context and genomic target coordinates.",
    count: 150_000,
    href: "/crispr",
    Icon: CrisprIcon,
  },
  {
    key: "genome",
    label: "Genomes",
    description: "Complete assembled genomes with assembly-level metadata.",
    count: 50_000,
    href: "/genomes",
    Icon: GenomeIcon,
  },
];
