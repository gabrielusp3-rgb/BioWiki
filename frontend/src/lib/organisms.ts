import type { Organism, OrganismGroup } from "@/types/organism";

/** NCBI Taxonomy browser URL for a given tax id (real, verifiable resource). */
export function ncbiTaxonomyUrl(taxId: number): string {
  return `https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id=${taxId}`;
}

/** Accent colour per organism group. */
export const GROUP_COLOR: Record<OrganismGroup, string> = {
  animal: "#00F2FF",
  plant: "#39FF14",
  fungus: "#FFFF00",
  bacteria: "#7C5CFF",
  archaea: "#FF00FF",
  virus: "#FF4444",
  protozoan: "#00F2FF",
};

export const GROUP_LABEL: Record<OrganismGroup, string> = {
  animal: "Animal",
  plant: "Plant",
  fungus: "Fungus",
  bacteria: "Bacteria",
  archaea: "Archaea",
  virus: "Virus",
  protozoan: "Protozoan",
};

function organism(
  data: Omit<Organism, "sequenceCount" | "imageUrl" | "links"> &
    Partial<Pick<Organism, "sequenceCount" | "imageUrl" | "links">>,
): Organism {
  return {
    sequenceCount: null,
    imageUrl: null,
    links: [
      { label: "View organism", url: `/organisms/${data.slug}` },
      { label: "NCBI Taxonomy", url: ncbiTaxonomyUrl(data.taxId), external: true },
    ],
    ...data,
  };
}

/**
 * REFERENCE ORGANISM IDENTITIES.
 *
 * These are real, well-established organisms with their canonical NCBI Taxonomy
 * IDs and lineages — factual public reference data, not fabricated records.
 * Sequence counts are intentionally `null` and are filled from the backend; the
 * UI never invents them. This list acts as a graceful fallback for the
 * `/organisms/featured` endpoint and demonstrates support for many organisms.
 */
export const REFERENCE_ORGANISMS: Organism[] = [
  organism({
    id: "9606",
    slug: "homo-sapiens",
    scientificName: "Homo sapiens",
    commonName: "Human",
    taxId: 9606,
    rank: "Species",
    group: "animal",
    category: "genome",
    lineage: ["Eukaryota", "Metazoa", "Chordata", "Mammalia", "Primates", "Hominidae", "Homo"],
  }),
  organism({
    id: "10090",
    slug: "mus-musculus",
    scientificName: "Mus musculus",
    commonName: "House mouse",
    taxId: 10090,
    rank: "Species",
    group: "animal",
    category: "genome",
    lineage: ["Eukaryota", "Metazoa", "Chordata", "Mammalia", "Rodentia", "Muridae", "Mus"],
  }),
  organism({
    id: "7955",
    slug: "danio-rerio",
    scientificName: "Danio rerio",
    commonName: "Zebrafish",
    taxId: 7955,
    rank: "Species",
    group: "animal",
    category: "genome",
    lineage: ["Eukaryota", "Metazoa", "Chordata", "Actinopteri", "Cypriniformes", "Danionidae", "Danio"],
  }),
  organism({
    id: "7227",
    slug: "drosophila-melanogaster",
    scientificName: "Drosophila melanogaster",
    commonName: "Fruit fly",
    taxId: 7227,
    rank: "Species",
    group: "animal",
    category: "genome",
    lineage: ["Eukaryota", "Metazoa", "Arthropoda", "Insecta", "Diptera", "Drosophilidae", "Drosophila"],
  }),
  organism({
    id: "6239",
    slug: "caenorhabditis-elegans",
    scientificName: "Caenorhabditis elegans",
    commonName: "Roundworm",
    taxId: 6239,
    rank: "Species",
    group: "animal",
    category: "genome",
    lineage: ["Eukaryota", "Metazoa", "Nematoda", "Chromadorea", "Rhabditida", "Rhabditidae", "Caenorhabditis"],
  }),
  organism({
    id: "4932",
    slug: "saccharomyces-cerevisiae",
    scientificName: "Saccharomyces cerevisiae",
    commonName: "Baker's yeast",
    taxId: 4932,
    rank: "Species",
    group: "fungus",
    category: "genome",
    lineage: ["Eukaryota", "Fungi", "Ascomycota", "Saccharomycetes", "Saccharomycetales", "Saccharomycetaceae", "Saccharomyces"],
  }),
  organism({
    id: "3702",
    slug: "arabidopsis-thaliana",
    scientificName: "Arabidopsis thaliana",
    commonName: "Thale cress",
    taxId: 3702,
    rank: "Species",
    group: "plant",
    category: "genome",
    lineage: ["Eukaryota", "Viridiplantae", "Streptophyta", "Magnoliopsida", "Brassicales", "Brassicaceae", "Arabidopsis"],
  }),
  organism({
    id: "562",
    slug: "escherichia-coli",
    scientificName: "Escherichia coli",
    commonName: "E. coli",
    taxId: 562,
    rank: "Species",
    group: "bacteria",
    category: "genome",
    lineage: ["Bacteria", "Pseudomonadota", "Gammaproteobacteria", "Enterobacterales", "Enterobacteriaceae", "Escherichia"],
  }),
  organism({
    id: "1423",
    slug: "bacillus-subtilis",
    scientificName: "Bacillus subtilis",
    commonName: "Hay bacillus",
    taxId: 1423,
    rank: "Species",
    group: "bacteria",
    category: "genome",
    lineage: ["Bacteria", "Bacillota", "Bacilli", "Bacillales", "Bacillaceae", "Bacillus"],
  }),
  organism({
    id: "2697049",
    slug: "sars-cov-2",
    scientificName: "Severe acute respiratory syndrome coronavirus 2",
    commonName: "SARS-CoV-2",
    taxId: 2697049,
    rank: "Species",
    group: "virus",
    category: "virus",
    lineage: ["Riboviria", "Orthornavirae", "Pisuviricota", "Pisoniviricetes", "Nidovirales", "Coronaviridae", "Betacoronavirus"],
  }),
  organism({
    id: "11676",
    slug: "hiv-1",
    scientificName: "Human immunodeficiency virus 1",
    commonName: "HIV-1",
    taxId: 11676,
    rank: "Species",
    group: "virus",
    category: "virus",
    lineage: ["Riboviria", "Pararnavirae", "Artverviricota", "Revtraviricetes", "Ortervirales", "Retroviridae", "Lentivirus"],
  }),
  organism({
    id: "9031",
    slug: "gallus-gallus",
    scientificName: "Gallus gallus",
    commonName: "Chicken",
    taxId: 9031,
    rank: "Species",
    group: "animal",
    category: "genome",
    lineage: ["Eukaryota", "Metazoa", "Chordata", "Aves", "Galliformes", "Phasianidae", "Gallus"],
  }),
];
