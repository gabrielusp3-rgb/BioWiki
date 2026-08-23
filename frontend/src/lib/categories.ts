import { colors, glow, type CategoryKey } from "@/lib/design-tokens";

export type { CategoryKey };

interface CategoryMeta {
  key: CategoryKey;
  label: string;
  color: string;
  glow: string;
  description: string;
}

/**
 * Category registry — labels, colours and glow shadows for the six primary
 * biological categories defined in the MASTER_PROMPT.
 */
export const CATEGORY_META: Record<CategoryKey, CategoryMeta> = {
  dna: {
    key: "dna",
    label: "DNA",
    color: colors.category.dna,
    glow: glow.dna,
    description: "Deoxyribonucleic acid sequences",
  },
  rna: {
    key: "rna",
    label: "RNA",
    color: colors.category.rna,
    glow: glow.rna,
    description: "Ribonucleic acid sequences",
  },
  protein: {
    key: "protein",
    label: "Protein",
    color: colors.category.protein,
    glow: glow.protein,
    description: "Amino acid sequences",
  },
  crispr: {
    key: "crispr",
    label: "CRISPR",
    color: colors.category.crispr,
    glow: glow.crispr,
    description: "CRISPR guide sequences",
  },
  virus: {
    key: "virus",
    label: "Virus",
    color: colors.category.virus,
    glow: glow.virus,
    description: "Viral genomes and segments",
  },
  genome: {
    key: "genome",
    label: "Genome",
    color: colors.category.genome,
    glow: glow.genome,
    description: "Complete assembled genomes",
  },
};

export function getCategoryMeta(key: CategoryKey): CategoryMeta {
  return CATEGORY_META[key];
}

/** Accent colour for a category key, or a neutral fallback for unknown types. */
export function categoryColor(key: string): string {
  if (key in CATEGORY_META) return CATEGORY_META[key as CategoryKey].color;
  return "#8A8A8A";
}
