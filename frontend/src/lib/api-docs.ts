import { API_BASE_URL } from "./api";

/**
 * API reference copy for the in-app documentation pages.
 * Paths and limits must match backend/app/api/v1.
 * Examples use the configured public API, or /api/v1 when unset.
 */

export const API_BASE = API_BASE_URL || "/api/v1";

export type HttpMethod = "GET";

export interface EndpointParam {
  name: string;
  type: string;
  description: string;
  required?: boolean;
}

export interface ApiEndpoint {
  method: HttpMethod;
  path: string;
  summary: string;
  params: EndpointParam[];
}

export const API_ENDPOINTS: ApiEndpoint[] = [
  {
    method: "GET",
    path: "/sequences",
    summary: "List DNA, RNA or CRISPR records (type is required).",
    params: [
      { name: "type", type: "string", description: "dna | rna | crispr", required: true },
      { name: "q", type: "string", description: "Free text over name/accession" },
      { name: "organism", type: "string", description: "Organism name" },
      { name: "source", type: "string", description: "Source key (for example ncbi_genbank)" },
      { name: "limit", type: "integer", description: "Page size (default 20, max 100)" },
      { name: "cursor", type: "string", description: "Opaque nextCursor from a previous page" },
    ],
  },
  {
    method: "GET",
    path: "/sequences/{accession}",
    summary: "One sequence record, including residues.",
    params: [{ name: "accession", type: "string", description: "Sequence accession", required: true }],
  },
  {
    method: "GET",
    path: "/proteins",
    summary: "List protein records.",
    params: [
      { name: "q", type: "string", description: "Free text over name/accession" },
      { name: "organism", type: "string", description: "Organism name" },
      { name: "limit", type: "integer", description: "Page size (default 20, max 100)" },
      { name: "cursor", type: "string", description: "Opaque nextCursor from a previous page" },
    ],
  },
  {
    method: "GET",
    path: "/viruses",
    summary: "List viral sequence records.",
    params: [
      { name: "q", type: "string", description: "Free text over name/accession" },
      { name: "family", type: "string", description: "Viral family" },
      { name: "limit", type: "integer", description: "Page size (default 20, max 100)" },
      { name: "cursor", type: "string", description: "Opaque nextCursor from a previous page" },
    ],
  },
  {
    method: "GET",
    path: "/organisms",
    summary: "List organisms.",
    params: [
      { name: "group", type: "string", description: "Optional organism group filter" },
      { name: "limit", type: "integer", description: "Page size (default 20, max 100)" },
      { name: "cursor", type: "string", description: "Opaque nextCursor from a previous page" },
    ],
  },
  {
    method: "GET",
    path: "/genomes",
    summary: "List genome assemblies.",
    params: [
      { name: "q", type: "string", description: "Free text over accession/name" },
      { name: "assembly_level", type: "string", description: "complete | chromosome | scaffold | contig" },
      { name: "limit", type: "integer", description: "Page size (default 20, max 100)" },
      { name: "cursor", type: "string", description: "Opaque nextCursor from a previous page" },
    ],
  },
  {
    method: "GET",
    path: "/publications",
    summary: "List bibliographic records stored in the catalogue.",
    params: [
      { name: "q", type: "string", description: "Free text over title or abstract" },
      { name: "accession", type: "string", description: "Only publications linked to this accession" },
      { name: "organism", type: "string", description: "Only publications linked to this organism" },
      { name: "limit", type: "integer", description: "Page size (default 20, max 100)" },
      { name: "cursor", type: "string", description: "Opaque nextCursor from a previous page" },
    ],
  },
  {
    method: "GET",
    path: "/publications/{pubmed_id}",
    summary: "One publication by PubMed ID, including linked sequence accessions.",
    params: [
      { name: "pubmed_id", type: "integer", description: "PubMed identifier", required: true },
    ],
  },
  {
    method: "GET",
    path: "/search",
    summary: "Full-text search over sequences in PostgreSQL.",
    params: [
      { name: "q", type: "string", description: "Search query", required: true },
      { name: "types", type: "string", description: "Optional comma-separated sequence types" },
      { name: "limit", type: "integer", description: "Page size (default 20, max 100)" },
      { name: "cursor", type: "string", description: "Opaque nextCursor from a previous page" },
    ],
  },
  {
    method: "GET",
    path: "/download/sequence/{accession}",
    summary: "Export one record (FASTA, GenBank or JSON).",
    params: [
      { name: "accession", type: "string", description: "Sequence accession", required: true },
      { name: "format", type: "string", description: "fasta | genbank | json (default fasta)" },
    ],
  },
];

export interface CodeSample {
  id: string;
  label: string;
  language: string;
  code: string;
}

export const REQUEST_SAMPLES: CodeSample[] = [
  {
    id: "curl",
    label: "cURL",
    language: "bash",
    code: `curl "${API_BASE}/search?q=insulin&types=protein&limit=20"
# If API_KEYS is set on the server, also send: -H "X-API-Key: $BIOWIKI_API_KEY"`,
  },
  {
    id: "javascript",
    label: "JavaScript",
    language: "javascript",
    code: `const res = await fetch(
  "${API_BASE}/search?q=insulin&types=protein&limit=20"
);
const data = await res.json();
console.log(data.total, data.results);`,
  },
  {
    id: "python",
    label: "Python",
    language: "python",
    code: `import requests

res = requests.get(
    "${API_BASE}/search",
    params={"q": "insulin", "types": "protein", "limit": 20},
)
data = res.json()
print(data["total"], data["results"])`,
  },
];

export interface FormatSample {
  id: string;
  label: string;
  language: string;
  code: string;
}

/** Format specifications (shapes, not fabricated records). */
export const FORMAT_SAMPLES: FormatSample[] = [
  {
    id: "json",
    label: "JSON",
    language: "json",
    code: `{
  "query": "insulin",
  "total": <integer>,
  "results": [
    {
      "accession": "<string>",
      "title": "<string>",
      "type": "protein",
      "organism": "<string>",
      "source": "<string>",
      "length": <integer>,
      "category": "protein"
    }
  ],
  "nextCursor": "<string|null>"
}`,
  },
  {
    id: "fasta",
    label: "FASTA",
    language: "text",
    code: `>{accession} {description} [{organism}]
{sequence residues, 60–80 characters per line}
{continued...}`,
  },
  {
    id: "csv",
    label: "CSV",
    language: "text",
    code: `accession,title,type,organism,source,length
# one row per record, values escaped per RFC 4180`,
  },
];

export interface ApiFeature {
  title: string;
  description: string;
}

export const API_FEATURES: ApiFeature[] = [
  {
    title: "Authentication",
    description:
      "Optional. If API_KEYS is empty the API is open. If keys are set, send X-API-Key.",
  },
  {
    title: "Rate limits",
    description:
      "Default 120 requests per 60 seconds per API process (RATE_LIMIT_*). Health is exempt.",
  },
  {
    title: "Formats",
    description:
      "JSON on list and search endpoints. Exports: FASTA, CSV, JSON, GenBank via /download.",
  },
];
