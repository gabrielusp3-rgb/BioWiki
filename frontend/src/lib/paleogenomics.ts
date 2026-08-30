import type {
  DeextinctionStatus,
  EvidenceLevel,
  ExtinctionStatus,
  PaleogenomicSubsection,
} from "@/types/paleogenomics";

export const SUBSECTION_LABEL: Record<PaleogenomicSubsection, string> = {
  extinct_species: "Extinct species",
  archaic_hominin: "Archaic hominins",
  ancient_dna: "Ancient DNA",
  archaic_introgression: "Archaic introgression",
};

export const EXTINCTION_LABEL: Record<ExtinctionStatus, string> = {
  extinct: "Extinct",
  extinct_prehistoric: "Prehistoric extinction",
  extinct_historic: "Historic extinction",
  archaic_hominin: "Archaic hominin",
};

export const EVIDENCE_LABEL: Record<EvidenceLevel, string> = {
  consensus: "Consensus",
  strong_evidence: "Strong evidence",
  supported_hypothesis: "Supported hypothesis",
  debated: "Debated",
  unknown: "Unknown / insufficient evidence",
};

export const DEEXTINCTION_LABEL: Record<DeextinctionStatus, string> = {
  no_active_program: "No active program",
  research_discussion: "Research discussion",
  active_research_program: "Active research program",
  genome_engineering_research: "Genome-engineering research",
  reproductive_technology_research: "Reproductive-technology research",
  proxy_trait_engineering: "Proxy / trait engineering",
  reintroduction_planning: "Reintroduction planning",
  unknown: "Unknown",
};

export function labelOf(
  map: Record<string, string>,
  value: string | null | undefined,
): string {
  if (!value) return "—";
  return map[value] ?? value.replaceAll("_", " ");
}

export function doiUrl(doi: string): string {
  return `https://doi.org/${doi.replace(/^https?:\/\/(dx\.)?doi\.org\//i, "")}`;
}
