import type { CategoryKey } from "@/lib/design-tokens";
import type { ComplexityLevel, SearchType } from "@/types/search";

interface SearchTypeMeta {
  type: SearchType;
  label: string;
  /** Category colour used to tint the scope, when applicable. */
  category?: CategoryKey;
  hint: string;
}

/** The nine searchable dimensions. These are domain scopes, not data records. */
export const SEARCH_TYPES: SearchTypeMeta[] = [
  { type: "gene", label: "Gene", hint: "Gene symbols and identifiers" },
  { type: "protein", label: "Protein", category: "protein", hint: "Protein names and UniProt IDs" },
  { type: "dna", label: "DNA", category: "dna", hint: "Nucleotide sequences" },
  { type: "rna", label: "RNA", category: "rna", hint: "Transcripts and RNA classes" },
  { type: "virus", label: "Virus", category: "virus", hint: "Viral genomes and segments" },
  { type: "crispr", label: "CRISPR", category: "crispr", hint: "Guide RNAs and targets" },
  { type: "genome", label: "Genome", category: "genome", hint: "Assembled genomes" },
  { type: "accession", label: "Accession", hint: "e.g. NM_000546, P04637" },
  { type: "taxonomy", label: "Taxonomy", hint: "Organisms and lineages" },
];

/** Public data sources the ingestion layer is designed to connect to. */
export const SEARCH_SOURCES: { value: string; label: string }[] = [
  { value: "all", label: "All sources" },
  { value: "ncbi_genbank", label: "NCBI GenBank" },
  { value: "ncbi_refseq", label: "NCBI RefSeq" },
  { value: "uniprot", label: "UniProt" },
  { value: "ensembl", label: "Ensembl" },
  { value: "pdb", label: "Protein Data Bank" },
  { value: "ena", label: "ENA" },
];

export const CATEGORY_OPTIONS: { value: CategoryKey | "all"; label: string }[] = [
  { value: "all", label: "All categories" },
  { value: "dna", label: "DNA" },
  { value: "rna", label: "RNA" },
  { value: "protein", label: "Protein" },
  { value: "crispr", label: "CRISPR" },
  { value: "virus", label: "Virus" },
  { value: "genome", label: "Genome" },
];

export const COMPLEXITY_OPTIONS: { value: ComplexityLevel; label: string }[] = [
  { value: "any", label: "Any complexity" },
  { value: "low", label: "Low" },
  { value: "medium", label: "Medium" },
  { value: "high", label: "High" },
];
