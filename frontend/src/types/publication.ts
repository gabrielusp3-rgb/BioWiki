/**
 * Scientific publication records served by `/publications`.
 * Every field mirrors the real bibliographic record (PubMed / source
 * REFERENCE blocks) — nothing is synthesised client-side.
 */
export interface Publication {
  id: string;
  pubmedId: number | null;
  doi: string | null;
  pmcId: string | null;
  title: string;
  abstract: string | null;
  authors: string[];
  journal: string | null;
  year: number | null;
  volume: string | null;
  pages: string | null;
  url: string | null;
}

export interface PublicationDetail extends Publication {
  /** Accessions of sequence records linked to this publication. */
  sequenceAccessions: string[];
}

export interface PublicationListResponse {
  results: Publication[];
  total: number;
  nextCursor: string | null;
}
