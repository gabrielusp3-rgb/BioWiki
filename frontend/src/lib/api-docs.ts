/**
 * Export format shapes for the Downloads page (not fabricated records).
 */

export interface FormatSample {
  id: string;
  label: string;
  language: string;
  code: string;
}

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
