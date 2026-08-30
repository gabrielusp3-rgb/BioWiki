"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Badge, Button, Skeleton } from "@/components/ui";
import { ExternalIcon } from "@/components/ui/Icons";
import { isApiConfigured } from "@/lib/api";
import { ncbiTaxonomyUrl } from "@/lib/organisms";
import {
  DEEXTINCTION_LABEL,
  EVIDENCE_LABEL,
  EXTINCTION_LABEL,
  SUBSECTION_LABEL,
  doiUrl,
  labelOf,
} from "@/lib/paleogenomics";
import { formatStatistic } from "@/lib/statistics";
import {
  getPaleogenomicsSpecies,
  listIntrogression,
  listPaleogenomicsGenomes,
  listPaleogenomicsProjects,
  listPaleogenomicsPublications,
  listPaleogenomicsSequences,
} from "@/services/paleogenomicsService";
import type { Publication } from "@/types/publication";
import type {
  PaleogenomicClaim,
  PaleogenomicIntrogression,
  PaleogenomicProject,
  PaleogenomicSequenceRow,
  PaleogenomicSpeciesDetail,
} from "@/types/paleogenomics";
import type { GenomeAssembly } from "@/types/sequence";

type Status = "loading" | "ready" | "notfound" | "unavailable" | "error";

function ClaimBlock({ claim }: { claim: PaleogenomicClaim }) {
  return (
    <section id={claim.sectionKey} className="glass hairline flex flex-col gap-4 p-6">
      <div className="flex flex-wrap items-baseline justify-between gap-3">
        <h2 className="font-display text-xl font-semibold text-content-primary">{claim.title}</h2>
        <span className="font-mono text-[11px] uppercase tracking-wider text-content-muted">
          {labelOf(EVIDENCE_LABEL, claim.evidenceLevel)}
        </span>
      </div>
      <p className="whitespace-pre-wrap text-sm leading-relaxed text-content-secondary">
        {claim.body}
      </p>
      {claim.sources.length > 0 && (
        <ul className="flex flex-col gap-2 border-t border-glass-divider pt-3 text-xs">
          {claim.sources.map((source, index) => {
            const href = source.pubmedId
              ? `/publications/${source.pubmedId}`
              : source.doi
                ? doiUrl(source.doi)
                : source.url;
            const label =
              source.label ||
              (source.pubmedId
                ? `PMID ${source.pubmedId}`
                : source.doi
                  ? `DOI ${source.doi}`
                  : source.url || "Source");
            return (
              <li key={`${claim.sectionKey}-${index}`}>
                {href ? (
                  <Link
                    href={href}
                    className="text-content-secondary hover:text-content-primary"
                    {...(href.startsWith("http")
                      ? { target: "_blank", rel: "noopener noreferrer" }
                      : {})}
                  >
                    {label}
                  </Link>
                ) : (
                  <span className="text-content-muted">{label}</span>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}

export function PaleogenomicsProfileContent({ slug }: { slug: string }) {
  const [status, setStatus] = useState<Status>("loading");
  const [detail, setDetail] = useState<PaleogenomicSpeciesDetail | null>(null);
  const [sequences, setSequences] = useState<PaleogenomicSequenceRow[]>([]);
  const [seqTotal, setSeqTotal] = useState(0);
  const [seqCursor, setSeqCursor] = useState<string | null>(null);
  const [publications, setPublications] = useState<Publication[]>([]);
  const [pubTotal, setPubTotal] = useState(0);
  const [pubCursor, setPubCursor] = useState<string | null>(null);
  const [genomes, setGenomes] = useState<GenomeAssembly[]>([]);
  const [projects, setProjects] = useState<PaleogenomicProject[]>([]);
  const [introgression, setIntrogression] = useState<PaleogenomicIntrogression[]>([]);
  const [introNote, setIntroNote] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    setStatus("loading");
    if (!isApiConfigured) {
      setStatus("unavailable");
      return;
    }
    getPaleogenomicsSpecies(slug, controller.signal)
      .then(async (record) => {
        if (controller.signal.aborted) return;
        if (record === null) {
          setStatus("notfound");
          return;
        }
        setDetail(record);
        const archaic =
          record.subsection === "archaic_hominin"
            ? record.slug.includes("neanderthal")
              ? "neanderthal"
              : record.slug.includes("denisova")
                ? "denisovan"
                : undefined
            : undefined;
        const [seq, pubs, gnm, proj, intro] = await Promise.all([
          listPaleogenomicsSequences(slug, { limit: 20, signal: controller.signal }),
          listPaleogenomicsPublications(slug, { limit: 20, signal: controller.signal }),
          listPaleogenomicsGenomes(slug, { limit: 20, signal: controller.signal }),
          listPaleogenomicsProjects(slug, { limit: 20, signal: controller.signal }),
          archaic
            ? listIntrogression({
                archaicSource: archaic,
                limit: 20,
                signal: controller.signal,
              })
            : Promise.resolve(null),
        ]);
        if (controller.signal.aborted) return;
        setSequences(seq.results);
        setSeqTotal(seq.total);
        setSeqCursor(seq.nextCursor);
        setPublications(pubs.results);
        setPubTotal(pubs.total);
        setPubCursor(pubs.nextCursor);
        setGenomes(gnm.results);
        setProjects(proj.results);
        if (intro) {
          setIntrogression(intro.results);
          setIntroNote(intro.note);
        }
        setStatus("ready");
      })
      .catch(() => {
        if (!controller.signal.aborted) setStatus("error");
      });
    return () => controller.abort();
  }, [slug]);

  if (status === "loading") {
    return (
      <div className="flex flex-col gap-4">
        <Skeleton height={160} />
        <Skeleton height={240} />
        <Skeleton height={240} />
      </div>
    );
  }

  if (status === "unavailable") {
    return (
      <div className="glass hairline p-10 text-center text-sm text-content-secondary">
        Species profiles appear once the sequence database is connected.
      </div>
    );
  }

  if (status === "notfound") {
    return (
      <div className="glass hairline p-10 text-center text-sm text-content-secondary">
        No Paleogenomics profile exists for this identifier. Absence of a page is not a claim
        that authentic DNA exists.
      </div>
    );
  }

  if (status === "error" || !detail) {
    return (
      <div className="glass hairline border-state-danger/40 p-10 text-center text-sm text-state-danger">
        This profile is temporarily unavailable.
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-10">
      <header className="flex flex-col gap-4">
        <div className="flex flex-wrap items-center gap-3">
          <Badge tone="neutral">{labelOf(SUBSECTION_LABEL, detail.subsection)}</Badge>
          {detail.extinctionStatus && (
            <Badge tone="neutral">{labelOf(EXTINCTION_LABEL, detail.extinctionStatus)}</Badge>
          )}
          <a
            href={ncbiTaxonomyUrl(detail.taxId)}
            target="_blank"
            rel="noopener noreferrer"
            className="ml-auto flex items-center gap-2 border border-glass-border px-3 py-1.5 font-mono text-xs text-content-secondary hover:text-content-primary"
          >
            taxid:{detail.taxId}
            <ExternalIcon className="h-3.5 w-3.5" />
          </a>
        </div>
        <h1 className="font-display text-3xl font-bold tracking-tightest text-content-primary">
          {detail.commonName}
        </h1>
        <p className="font-body text-base italic text-content-secondary">{detail.scientificName}</p>
        <p className="text-sm text-content-secondary">
          {[detail.geologicPeriod, detail.geographicRegion, detail.extinctionDateText]
            .filter(Boolean)
            .join(" · ")}
        </p>
        {detail.taxonomicUncertainty && (
          <p className="glass hairline p-4 text-sm text-content-secondary">
            {detail.taxonomicUncertainty}
          </p>
        )}
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <div>
            <p className="font-display text-xl font-bold tabular-nums">{formatStatistic(detail.sequenceCount)}</p>
            <p className="text-[10px] uppercase tracking-wider text-content-muted">Sequences</p>
          </div>
          <div>
            <p className="font-display text-xl font-bold tabular-nums">{formatStatistic(detail.mitogenomeCount)}</p>
            <p className="text-[10px] uppercase tracking-wider text-content-muted">Complete mt genomes</p>
          </div>
          <div>
            <p className="font-display text-xl font-bold tabular-nums">{formatStatistic(detail.assemblyCount)}</p>
            <p className="text-[10px] uppercase tracking-wider text-content-muted">Assemblies</p>
          </div>
          <div>
            <p className="font-display text-xl font-bold tabular-nums">{formatStatistic(detail.publicationCount)}</p>
            <p className="text-[10px] uppercase tracking-wider text-content-muted">Publications</p>
          </div>
        </div>
        <p className="text-xs text-content-muted">
          Preferred discovery target {detail.preferredSequenceTarget} is a curation goal, not a quota.
          Stored count is {detail.sequenceCount}. De-extinction:{" "}
          {labelOf(DEEXTINCTION_LABEL, detail.deextinctionStatus)}. Last reviewed{" "}
          {detail.lastReviewedOn ?? "—"}.
        </p>
        <div className="flex flex-wrap gap-3">
          <Link
            href={`/organisms/${detail.organism.slug}`}
            className="border border-glass-border px-3 py-2 text-xs uppercase tracking-wide text-content-secondary hover:text-content-primary"
          >
            Organism record
          </Link>
          <Link
            href={`/search?q=${encodeURIComponent(detail.scientificName)}`}
            className="border border-glass-border px-3 py-2 text-xs uppercase tracking-wide text-content-secondary hover:text-content-primary"
          >
            Search catalogue
          </Link>
        </div>
      </header>

      <nav aria-label="Profile sections" className="flex flex-wrap gap-2">
        {detail.claims.map((claim) => (
          <a
            key={claim.sectionKey}
            href={`#${claim.sectionKey}`}
            className="border border-glass-border px-3 py-1.5 text-[11px] uppercase tracking-wide text-content-muted hover:text-content-primary"
          >
            {claim.title}
          </a>
        ))}
      </nav>

      {detail.claims.map((claim) => (
        <ClaimBlock key={claim.sectionKey} claim={claim} />
      ))}

      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="eyebrow">Sequences</h2>
          <span className="font-mono text-[11px] text-content-muted">
            {formatStatistic(seqTotal)} · not raw SRA reads
          </span>
        </div>
        {sequences.length === 0 ? (
          <div className="glass hairline p-8 text-sm text-content-secondary">
            No palaeogenomic sequence records are catalogued for this taxon. That does not invent DNA.
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            {sequences.map((row) => (
              <Link
                key={row.id}
                href={`/sequences/${encodeURIComponent(row.accession)}`}
                className="glass hairline flex flex-col gap-1 px-5 py-3.5 hover:border-white/20"
              >
                <span className="flex items-center gap-4">
                  <Badge category={row.seqType === "protein" ? "protein" : row.seqType === "rna" ? "rna" : "dna"} />
                  <span className="min-w-0 flex-1 truncate text-sm">{row.name}</span>
                  <span className="hidden font-mono text-xs text-content-muted sm:block">
                    {row.accession}
                  </span>
                  {row.isCompleteMitogenome && (
                    <span className="font-mono text-[10px] uppercase text-content-muted">complete mt</span>
                  )}
                </span>
                {(row.specimenLabel || row.biosample || row.bioproject) && (
                  <span className="font-mono text-[10px] text-content-muted">
                    {[
                      row.specimenLabel ? `specimen ${row.specimenLabel}` : null,
                      row.biosample,
                      row.bioproject,
                    ]
                      .filter(Boolean)
                      .join(" · ")}
                  </span>
                )}
              </Link>
            ))}
            {seqCursor && (
              <Button
                variant="glass"
                onClick={async () => {
                  const page = await listPaleogenomicsSequences(slug, { cursor: seqCursor });
                  setSequences((prev) => [...prev, ...page.results]);
                  setSeqCursor(page.nextCursor);
                }}
              >
                Load more sequences
              </Button>
            )}
          </div>
        )}
      </section>

      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="eyebrow">Genome assemblies</h2>
          <span className="font-mono text-[11px] text-content-muted">
            {formatStatistic(detail.assemblyCount)} · genome_records, not Sequence rows
          </span>
        </div>
        {genomes.length === 0 ? (
          <div className="glass hairline p-8 text-sm text-content-secondary">
            No authentic assembly metadata is stored for this taxon.
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            {genomes.map((genome) => (
              <Link
                key={genome.id}
                href={`/genomes/${encodeURIComponent(genome.accession)}`}
                className="glass hairline flex items-center justify-between gap-4 px-5 py-4 hover:border-white/20"
              >
                <span className="font-mono text-sm">{genome.accession}</span>
                <span className="text-xs text-content-secondary">{genome.assemblyLevel}</span>
              </Link>
            ))}
          </div>
        )}
      </section>

      <section>
        <h2 className="eyebrow mb-3">Projects and samples</h2>
        {projects.length === 0 ? (
          <div className="glass hairline p-8 text-sm text-content-secondary">
            No BioProject/BioSample metadata rows are stored. Raw sequencing reads are not imported
            as catalogue sequences.
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            {projects.map((project, index) => (
              <div key={`${project.bioproject}-${project.biosample}-${index}`} className="glass hairline p-5 text-sm">
                <p className="font-mono text-xs text-content-muted">
                  {[project.bioproject, project.biosample, project.runAccession]
                    .filter(Boolean)
                    .join(" · ")}
                </p>
                {project.libraryStrategy && (
                  <p className="mt-1 text-content-secondary">{project.libraryStrategy}</p>
                )}
                {project.controlledAccess && (
                  <p className="mt-2 text-xs text-content-muted">Controlled-access dataset — metadata only.</p>
                )}
                {project.sourceUrl && (
                  <a
                    href={project.sourceUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="mt-2 inline-flex items-center gap-2 text-xs text-content-secondary hover:text-content-primary"
                  >
                    Source
                    <ExternalIcon className="h-3 w-3" />
                  </a>
                )}
              </div>
            ))}
          </div>
        )}
      </section>

      {(detail.introgressionCount !== null || introgression.length > 0) && (
        <section id="introgression">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="eyebrow">Archaic introgression in living humans</h2>
            <span className="font-mono text-[11px] text-content-muted">
              {formatStatistic(detail.introgressionCount ?? introgression.length)} loci
            </span>
          </div>
          <p className="mb-4 text-sm text-content-secondary">
            {detail.introgressionNote ?? introNote} These are{" "}
            <em>Homo sapiens</em> genomic loci with evidence of archaic ancestry, not DNA
            physically extracted from a Neanderthal or Denisovan specimen.
          </p>
          {introgression.length === 0 ? (
            <div className="glass hairline p-8 text-sm text-content-secondary">
              No gene-level introgression rows are stored for this archaic source.
            </div>
          ) : (
            <div className="flex flex-col gap-3">
              {introgression.map((row) => (
                <div key={row.id} className="glass hairline flex flex-col gap-2 p-5">
                  <div className="flex flex-wrap items-baseline justify-between gap-2">
                    <span className="font-display text-sm text-content-primary">
                      {row.geneName ?? row.locusName}
                    </span>
                    <span className="font-mono text-[11px] uppercase text-content-muted">
                      {row.archaicSource} → {row.modernScientificName}
                    </span>
                  </div>
                  <p className="text-sm text-content-secondary">{row.evidenceNotes}</p>
                  {!row.referenceBuild && (
                    <p className="text-xs text-content-muted">
                      Coordinates omitted: no genome build is stored for this row.
                    </p>
                  )}
                  {row.pubmedId && (
                    <Link
                      href={`/publications/${row.pubmedId}`}
                      className="text-xs text-content-secondary hover:text-content-primary"
                    >
                      PMID {row.pubmedId}
                    </Link>
                  )}
                </div>
              ))}
            </div>
          )}
        </section>
      )}

      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="eyebrow">Scientific literature</h2>
          <span className="font-mono text-[11px] text-content-muted">
            {formatStatistic(pubTotal)}
          </span>
        </div>
        {publications.length === 0 ? (
          <div className="glass hairline p-8 text-sm text-content-secondary">
            No linked publication rows yet. Claim citations above still point at source identifiers.
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            {publications.map((publication) => {
              const href = publication.pubmedId
                ? `/publications/${publication.pubmedId}`
                : publication.doi
                  ? doiUrl(publication.doi)
                  : publication.url;
              return href ? (
                <Link
                  key={publication.id}
                  href={href}
                  className="glass hairline px-5 py-4 text-sm hover:border-white/20"
                >
                  {publication.title}
                  {publication.pubmedId && (
                    <span className="mt-1 block font-mono text-[11px] text-content-muted">
                      PMID {publication.pubmedId}
                    </span>
                  )}
                </Link>
              ) : (
                <div key={publication.id} className="glass hairline px-5 py-4 text-sm">
                  {publication.title}
                </div>
              );
            })}
            {pubCursor && (
              <Button
                variant="glass"
                onClick={async () => {
                  const page = await listPaleogenomicsPublications(slug, { cursor: pubCursor });
                  setPublications((prev) => [...prev, ...page.results]);
                  setPubCursor(page.nextCursor);
                }}
              >
                Load more publications
              </Button>
            )}
          </div>
        )}
      </section>
    </div>
  );
}
