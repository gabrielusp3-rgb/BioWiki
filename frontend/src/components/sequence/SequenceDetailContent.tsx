"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Badge, Skeleton } from "@/components/ui";
import { ExternalIcon } from "@/components/ui/Icons";
import { SequenceViewer } from "@/components/viewer";
import { isApiConfigured } from "@/lib/api";
import type { CategoryKey } from "@/lib/design-tokens";
import { formatStatistic } from "@/lib/statistics";
import { getSequence, sequenceDownloadUrl } from "@/services/sequenceService";
import { listPublications } from "@/services/publicationService";
import type { Publication } from "@/types/publication";
import type { SequenceDetail } from "@/types/sequence";

const CATEGORY_OF_TYPE: Record<string, CategoryKey> = {
  dna: "dna",
  rna: "rna",
  protein: "protein",
  peptide: "protein",
  crispr: "crispr",
  virus: "virus",
  genome: "genome",
};

const TYPE_LABEL: Record<string, string> = {
  dna: "DNA",
  rna: "RNA",
  protein: "Protein",
  peptide: "Peptide",
  crispr: "CRISPR",
  virus: "Virus",
  genome: "Genome",
};

type Status = "loading" | "ready" | "notfound" | "unavailable" | "error";

function MetaItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-1 border border-glass-divider p-3">
      <span className="eyebrow">{label}</span>
      <span className="break-words font-mono text-sm text-content-primary">{value}</span>
    </div>
  );
}

function gcPercent(gc: number | null | undefined): string | null {
  if (gc === null || gc === undefined) return null;
  return `${(gc * 100).toFixed(2)} %`;
}

function buildMeta(seq: SequenceDetail): { label: string; value: string }[] {
  const length = seq.length ?? seq.guideLength;
  const unit = seq.type === "protein" || seq.type === "peptide" ? "aa" : "bp";
  const items: ({ label: string; value: string | null | undefined } | null)[] = [
    { label: "Accession", value: seq.version ? `${seq.accession}.${seq.version}` : seq.accession },
    { label: "Type", value: TYPE_LABEL[seq.type] ?? seq.type },
    { label: "Organism", value: seq.organism },
    seq.taxId ? { label: "NCBI Tax ID", value: String(seq.taxId) } : null,
    length ? { label: "Length", value: `${formatStatistic(length)} ${unit}` } : null,
    { label: "GC content", value: gcPercent(seq.gcContent) },
    { label: "Source", value: seq.source },
    { label: "Gene", value: seq.geneName ?? seq.gene ?? seq.targetGene },
    { label: "Chromosome", value: seq.chromosome },
    // Category-specific real attributes
    seq.moleculeType ? { label: "Molecule type", value: seq.moleculeType } : null,
    seq.strand && seq.strand !== "unknown" ? { label: "Strand", value: seq.strand } : null,
    seq.rnaClass ? { label: "RNA class", value: seq.rnaClass } : null,
    seq.isCoding !== undefined && seq.type === "rna"
      ? { label: "Coding", value: seq.isCoding ? "Yes" : "No" }
      : null,
    seq.reviewed !== undefined && (seq.type === "protein" || seq.type === "peptide")
      ? { label: "Reviewed", value: seq.reviewed ? "Yes (Swiss-Prot)" : "No" }
      : null,
    seq.molecularWeight ? { label: "Molecular weight", value: `${formatStatistic(Math.round(seq.molecularWeight))} Da` } : null,
    seq.system ? { label: "Cas system", value: seq.system } : null,
    seq.pam ? { label: "PAM", value: seq.pam } : null,
    seq.family ? { label: "Family", value: seq.family } : null,
    seq.genomeType ? { label: "Genome type", value: seq.genomeType } : null,
    seq.host ? { label: "Host", value: seq.host } : null,
    seq.segment ? { label: "Segment", value: seq.segment } : null,
    seq.updatedAt
      ? { label: "Updated", value: new Date(seq.updatedAt).toISOString().slice(0, 10) }
      : null,
  ];
  return items.filter(
    (item): item is { label: string; value: string } => Boolean(item && item.value),
  );
}

/** Render one verbatim annotation value without inventing structure. */
function annotationText(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  if (Array.isArray(value) && value.every((v) => typeof v === "string")) {
    return (value as string[]).join(", ");
  }
  return JSON.stringify(value, null, 1);
}

function PublicationRow({ publication }: { publication: Publication }) {
  const authors =
    publication.authors.length > 3
      ? `${publication.authors.slice(0, 3).join(", ")} et al.`
      : publication.authors.join(", ");
  const line = [authors, publication.journal, publication.year].filter(Boolean).join(" · ");
  const body = (
    <>
      <span className="flex min-w-0 flex-1 flex-col gap-1">
        <span className="font-body text-sm text-content-primary">{publication.title}</span>
        {line && <span className="truncate text-xs text-content-secondary">{line}</span>}
      </span>
      {publication.pubmedId && (
        <span className="shrink-0 font-mono text-[11px] text-content-muted">
          PMID {publication.pubmedId}
        </span>
      )}
    </>
  );
  const className =
    "glass hairline flex w-full items-start gap-4 px-5 py-4 transition-colors hover:border-white/20";
  if (publication.pubmedId) {
    return (
      <Link href={`/publications/${publication.pubmedId}`} className={className}>
        {body}
      </Link>
    );
  }
  return <div className={className}>{body}</div>;
}

export function SequenceDetailContent({ accession }: { accession: string }) {
  const [status, setStatus] = useState<Status>(isApiConfigured ? "loading" : "unavailable");
  const [seq, setSeq] = useState<SequenceDetail | null>(null);
  const [publications, setPublications] = useState<Publication[]>([]);

  useEffect(() => {
    if (!isApiConfigured) return;
    const controller = new AbortController();
    setStatus("loading");
    getSequence(accession, controller.signal)
      .then((record) => {
        if (controller.signal.aborted) return;
        if (record === null) {
          setStatus("notfound");
          return;
        }
        setSeq(record);
        setStatus("ready");
      })
      .catch(() => {
        if (!controller.signal.aborted) setStatus("error");
      });
    listPublications({ accession, limit: 25, signal: controller.signal })
      .then((response) => {
        if (!controller.signal.aborted) setPublications(response.results);
      })
      .catch(() => {
        /* references section simply stays empty */
      });
    return () => controller.abort();
  }, [accession]);

  if (status === "loading") {
    return (
      <div className="flex flex-col gap-4">
        <Skeleton height={120} />
        <Skeleton height={420} />
      </div>
    );
  }

  if (status === "unavailable") {
    return (
      <div className="glass hairline p-10 text-center text-sm text-content-secondary">
        Record details are served from the database. Connect the backend to view
        this sequence.
      </div>
    );
  }

  if (status === "notfound") {
    return (
      <div className="glass hairline flex flex-col items-center gap-4 p-10 text-center">
        <p className="text-sm text-content-secondary">
          No record with accession{" "}
          <span className="font-mono text-content-primary">{accession}</span> exists
          in the database. Nothing is shown that does not exist.
        </p>
        <Link
          href="/search"
          className="border border-glass-border px-4 py-2 font-display text-xs font-semibold uppercase tracking-wide text-content-secondary transition-colors hover:border-white/30 hover:text-content-primary"
        >
          Search the database
        </Link>
      </div>
    );
  }

  if (status === "error" || !seq) {
    return (
      <div className="glass hairline border-state-danger/40 p-10 text-center text-sm text-state-danger">
        The record could not be loaded. Please try again.
      </div>
    );
  }

  const category = CATEGORY_OF_TYPE[seq.type] ?? "dna";
  const residues = seq.sequence ?? seq.guideSequence ?? null;
  const kind = seq.type === "protein" || seq.type === "peptide" ? "protein" : "nucleotide";
  const molecule =
    seq.type === "rna" || (seq.type === "virus" && seq.molecule === "rna") ? "rna" : "dna";
  const meta = buildMeta(seq);
  const annotations = Object.entries(seq.annotations ?? {});
  const header = seq.version
    ? `${seq.accession}.${seq.version} ${seq.name}`
    : `${seq.accession} ${seq.name}`;

  return (
    <div className="flex flex-col gap-8">
      {/* Identity */}
      <div className="glass hairline flex flex-col gap-4 p-6">
        <div className="flex flex-wrap items-center gap-3">
          <Badge category={category} dot>
            {TYPE_LABEL[seq.type] ?? seq.type}
          </Badge>
          <span className="font-mono text-sm text-content-secondary">{seq.accession}</span>
          {seq.sourceUrl && (
            <a
              href={seq.sourceUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="ml-auto flex items-center gap-2 border border-glass-border px-3 py-1.5 font-display text-[11px] font-semibold uppercase tracking-wide text-content-secondary transition-colors hover:border-white/30 hover:text-content-primary"
            >
              View at source
              <ExternalIcon className="h-3.5 w-3.5" />
            </a>
          )}
        </div>
        <h1 className="font-display text-2xl font-bold tracking-tightest text-content-primary">
          {seq.name}
        </h1>
        <p className="font-body text-sm italic text-content-secondary">
          {seq.taxId ? (
            <Link href={`/organisms/${seq.taxId}`} className="hover:text-content-primary">
              {seq.organism}
            </Link>
          ) : (
            seq.organism
          )}
        </p>
        {seq.description && seq.description !== seq.name && (
          <p className="font-body text-sm text-content-secondary">{seq.description}</p>
        )}
      </div>

      {/* Real metadata */}
      <section>
        <span className="eyebrow mb-3 block">Record</span>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
          {meta.map((item) => (
            <MetaItem key={item.label} label={item.label} value={item.value} />
          ))}
        </div>
      </section>

      {/* Sequence viewer */}
      <section>
        <span className="eyebrow mb-3 block">Sequence</span>
        <SequenceViewer
          header={header}
          title={seq.name}
          subtitle={seq.accession}
          sequence={residues}
          kind={kind}
          molecule={molecule}
          accent={category}
          filename={seq.accession}
          jsonPayload={seq}
          emptyMessage="Residues for this record have not been ingested yet — only verified sequence data is ever displayed."
        />
      </section>

      {/* Downloads */}
      <section>
        <span className="eyebrow mb-3 block">Downloads</span>
        <div className="flex flex-wrap gap-3">
          {(["fasta", "genbank", "json"] as const).map((format) => (
            <a
              key={format}
              href={sequenceDownloadUrl(seq.accession, format)}
              className="border border-glass-border px-4 py-2 font-display text-xs font-semibold uppercase tracking-wide text-content-secondary transition-colors hover:border-white/30 hover:text-content-primary"
            >
              {format === "genbank" ? "GenBank" : format.toUpperCase()}
            </a>
          ))}
        </div>
        <p className="mt-2 text-xs text-content-muted">
          Exports are generated from the database record — FASTA requires ingested residues.
        </p>
      </section>

      {/* Annotations (verbatim from the source record) */}
      {annotations.length > 0 && (
        <section>
          <span className="eyebrow mb-3 block">Annotation</span>
          <div className="glass hairline divide-y divide-glass-divider">
            {annotations.map(([key, value]) => (
              <div key={key} className="grid grid-cols-1 gap-1 px-5 py-3 sm:grid-cols-[200px_1fr] sm:gap-4">
                <span className="font-mono text-xs uppercase tracking-wider text-content-muted">
                  {key}
                </span>
                <span className="whitespace-pre-wrap break-words font-body text-sm text-content-secondary">
                  {annotationText(value)}
                </span>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* References */}
      {publications.length > 0 && (
        <section>
          <span className="eyebrow mb-3 block">References</span>
          <div className="flex flex-col gap-3">
            {publications.map((publication) => (
              <PublicationRow key={publication.id} publication={publication} />
            ))}
          </div>
        </section>
      )}

      {/* Protein cross-references */}
      {(seq.pdbIds?.length ?? 0) > 0 && (
        <section>
          <span className="eyebrow mb-3 block">PDB structures</span>
          <div className="flex flex-wrap gap-2">
            {seq.pdbIds!.map((pdbId) => (
              <a
                key={pdbId}
                href={`https://www.rcsb.org/structure/${pdbId}`}
                target="_blank"
                rel="noopener noreferrer"
                className="border border-glass-border px-3 py-1.5 font-mono text-xs text-content-secondary transition-colors hover:border-white/30 hover:text-content-primary"
              >
                {pdbId}
              </a>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
