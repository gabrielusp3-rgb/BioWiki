import type { CategoryKey } from "@/lib/design-tokens";

export type OrganismGroup =
  | "animal"
  | "plant"
  | "fungus"
  | "bacteria"
  | "archaea"
  | "virus"
  | "protozoan";

export interface OrganismLink {
  label: string;
  url: string;
  external?: boolean;
}

export interface Organism {
  id: string;
  slug: string;
  scientificName: string;
  commonName?: string;
  /** NCBI Taxonomy ID — the canonical, verifiable identifier. */
  taxId: number;
  rank: string;
  /** Ordered lineage from broad to specific. */
  lineage: string[];
  group: OrganismGroup;
  category?: CategoryKey;
  /**
   * Real record count from the backend. `null` means "not yet available" — the
   * UI shows a neutral state instead of ever inventing a number.
   */
  sequenceCount: number | null;
  /** Provided by the backend/media service; null renders the abstract emblem. */
  imageUrl?: string | null;
  links: OrganismLink[];
  extinctionStatus?: string | null;
  extinctionDateText?: string | null;
  geologicPeriod?: string | null;
  paleogenomicSlug?: string | null;
}
