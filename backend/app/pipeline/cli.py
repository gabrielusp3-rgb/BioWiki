"""BIOWIKI ingestion CLI — explicit, operator-driven imports of real data.

Nothing runs automatically. Examples:

    # NCBI GenBank/RefSeq nucleotide records (by accession or search)
    python -m app.pipeline.cli ncbi --accessions NM_000207.3 NM_007294.4
    python -m app.pipeline.cli ncbi --term "BRCA1[gene] AND human[orgn] AND refseq[filter]" --limit 20
    python -m app.pipeline.cli ncbi --db protein --accessions NP_000198.1

    # UniProt proteins
    python -m app.pipeline.cli uniprot --accessions P01308 P38398
    python -m app.pipeline.cli uniprot --query "gene:INS AND organism_id:9606 AND reviewed:true" --limit 10

    # ENA records
    python -m app.pipeline.cli ena --accessions BN000065

    # RCSB PDB entries (each polymer entity becomes a record)
    python -m app.pipeline.cli pdb --ids 1BOM 4HHB

    # Ensembl sequences
    python -m app.pipeline.cli ensembl --ids ENSG00000254647 --kind genomic

    # NCBI Datasets genome assemblies
    python -m app.pipeline.cli genomes --accessions GCF_000001405.40
    python -m app.pipeline.cli genomes --taxon "Escherichia coli" --limit 5

    # Rfam family members (ingested via NCBI with full provenance)
    python -m app.pipeline.cli rfam --family RF00001 --limit 10

    # PubMed articles / links
    python -m app.pipeline.cli pubmed --pmids 6318096 24270810
    python -m app.pipeline.cli pubmed --term "CRISPR[Title] AND Cas9[Title]" --limit 100
    python -m app.pipeline.cli pubmed --pmids 6318096 --link-accession NM_000207

    # Local files (FASTA/GenBank/JSON/CSV) — same flags as workers.runner
    python -m app.pipeline.cli file --file data/x.gb --source-key ncbi_genbank
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

from app.core.stdio import configure_utf8_stdio

configure_utf8_stdio()

from app.pipeline.logging import get_logger
from app.pipeline.models import ImportContext, ImportReport, ParsedOrganism
from app.pipeline.run_log import record_run
from app.pipeline.workers.import_worker import import_file

logger = get_logger("biowiki.pipeline.cli")


def _print_report(report: ImportReport) -> None:
    sys.stdout.write(json.dumps(report.as_dict(), indent=2, ensure_ascii=False) + "\n")
    sys.stdout.flush()


async def _cmd_ncbi(args: argparse.Namespace) -> ImportReport:
    from app.pipeline.fetchers import ncbi

    return await ncbi.ingest(
        args.accessions,
        term=args.term,
        db=args.db,
        limit=args.limit,
        seq_type=args.seq_type,
        batch_size=args.batch_size,
    )


async def _cmd_uniprot(args: argparse.Namespace) -> ImportReport:
    from app.pipeline.fetchers import uniprot

    return await uniprot.ingest(
        args.accessions, query=args.query, limit=args.limit, batch_size=args.batch_size
    )


async def _cmd_ena(args: argparse.Namespace) -> ImportReport:
    from app.pipeline.fetchers import ena

    return await ena.ingest(
        args.accessions, seq_type=args.seq_type, batch_size=args.batch_size
    )


async def _cmd_pdb(args: argparse.Namespace) -> ImportReport:
    from app.pipeline.fetchers import pdb

    return await pdb.ingest(args.ids, batch_size=args.batch_size)


async def _cmd_ensembl(args: argparse.Namespace) -> ImportReport:
    from app.pipeline.fetchers import ensembl

    return await ensembl.ingest(args.ids, kind=args.kind, batch_size=args.batch_size)


async def _cmd_genomes(args: argparse.Namespace) -> ImportReport:
    from app.pipeline.fetchers import datasets

    return await datasets.ingest(args.accessions, taxon=args.taxon, limit=args.limit)


async def _cmd_rfam(args: argparse.Namespace) -> ImportReport:
    from app.pipeline.fetchers import rfam

    return await rfam.ingest_family(
        args.family, limit=args.limit, batch_size=args.batch_size
    )


async def _cmd_pubmed(args: argparse.Namespace) -> ImportReport:
    from app.pipeline.fetchers import pubmed

    if args.link_accession:
        if not args.pmids:
            raise SystemExit("pubmed --link-accession requires --pmids")
        return await pubmed.link_sequence(args.link_accession, args.pmids)
    if args.term:
        return await pubmed.ingest_search(
            args.term, limit=args.limit, retstart=args.retstart
        )
    if not args.pmids:
        raise SystemExit("pubmed requires --pmids or --term")
    return await pubmed.ingest_pmids(args.pmids)


async def _cmd_sync(_: argparse.Namespace) -> dict:
    """Reconcile cached UI counters with the real rows and report the state."""
    from app.database.session import get_sessionmaker
    from app.services import sync_service

    async with get_sessionmaker()() as session:
        refreshed = await sync_service.refresh_counts(session)
        status = await sync_service.get_sync_status(session)
    return {"refreshed": refreshed, "status": status.model_dump(by_alias=True)}


async def _cmd_integrity(_: argparse.Namespace) -> dict:
    """Run every UI/DB/reference integrity check and report pass/fail."""
    from app.database.session import get_sessionmaker
    from app.services import sync_service

    async with get_sessionmaker()() as session:
        report = await sync_service.check_integrity(session)
    return report.model_dump(by_alias=True, mode="json")


async def _cmd_file(args: argparse.Namespace) -> ImportReport:
    organism = None
    if args.organism and args.tax_id:
        organism = ParsedOrganism(
            scientific_name=args.organism,
            tax_id=args.tax_id,
            common_name=args.common_name,
            group=args.group,
        )
    context = ImportContext(
        source_key=args.source_key,
        source_name=args.source_name,
        seq_type=args.seq_type,
        molecule=args.molecule,
        organism=organism,
    )
    async with record_run(
        args.source_key, "file_import", {"file": args.file, "format": args.fmt}
    ) as run:
        report = await import_file(
            args.file, context, fmt=args.fmt, batch_size=args.batch_size
        )
        run.set_report(report)
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m app.pipeline.cli",
        description="BIOWIKI ingestion of real biological data from public databases.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    def add_batch(p: argparse.ArgumentParser) -> None:
        p.add_argument("--batch-size", type=int, default=200)

    p = sub.add_parser("ncbi", help="NCBI GenBank/RefSeq via E-utilities.")
    p.add_argument("--accessions", nargs="*", default=None)
    p.add_argument("--term", default=None, help="Entrez search term.")
    p.add_argument("--db", choices=["nuccore", "protein"], default="nuccore")
    p.add_argument("--limit", type=int, default=100)
    p.add_argument("--seq-type", default=None, help="Override: dna|rna|protein|crispr|virus")
    add_batch(p)
    p.set_defaults(func=_cmd_ncbi)

    p = sub.add_parser("uniprot", help="UniProtKB proteins.")
    p.add_argument("--accessions", nargs="*", default=None)
    p.add_argument("--query", default=None)
    p.add_argument("--limit", type=int, default=100)
    add_batch(p)
    p.set_defaults(func=_cmd_uniprot)

    p = sub.add_parser("ena", help="EMBL-EBI ENA records.")
    p.add_argument("--accessions", nargs="+", required=True)
    p.add_argument("--seq-type", default=None)
    add_batch(p)
    p.set_defaults(func=_cmd_ena)

    p = sub.add_parser("pdb", help="RCSB PDB entries.")
    p.add_argument("--ids", nargs="+", required=True)
    add_batch(p)
    p.set_defaults(func=_cmd_pdb)

    p = sub.add_parser("ensembl", help="Ensembl sequences by stable ID.")
    p.add_argument("--ids", nargs="+", required=True)
    p.add_argument("--kind", choices=["genomic", "cds", "cdna", "protein"], default="genomic")
    add_batch(p)
    p.set_defaults(func=_cmd_ensembl)

    p = sub.add_parser("genomes", help="NCBI Datasets genome assemblies.")
    p.add_argument("--accessions", nargs="*", default=None)
    p.add_argument("--taxon", default=None)
    p.add_argument("--limit", type=int, default=20)
    p.set_defaults(func=_cmd_genomes)

    p = sub.add_parser("rfam", help="Rfam family members (via NCBI provenance).")
    p.add_argument("--family", required=True, help="Rfam accession, e.g. RF00001.")
    p.add_argument("--limit", type=int, default=25)
    add_batch(p)
    p.set_defaults(func=_cmd_rfam)

    p = sub.add_parser("pubmed", help="PubMed articles and sequence links.")
    p.add_argument("--pmids", nargs="*", default=None)
    p.add_argument("--term", default=None, help="PubMed Entrez search term.")
    p.add_argument("--limit", type=int, default=200)
    p.add_argument("--retstart", type=int, default=0)
    p.add_argument("--link-accession", default=None, help="Attach articles to this sequence.")
    p.set_defaults(func=_cmd_pubmed)

    p = sub.add_parser("file", help="Import a local FASTA/GenBank/JSON/CSV file.")
    p.add_argument("--file", required=True)
    p.add_argument("--format", dest="fmt", default=None)
    p.add_argument("--source-key", required=True)
    p.add_argument("--source-name", default=None)
    p.add_argument("--seq-type", default=None)
    p.add_argument("--molecule", default=None)
    p.add_argument("--organism", default=None)
    p.add_argument("--tax-id", type=int, default=None)
    p.add_argument("--common-name", default=None)
    p.add_argument("--group", default=None)
    add_batch(p)
    p.set_defaults(func=_cmd_file)

    p = sub.add_parser("sync", help="Reconcile cached UI counters with real rows.")
    p.set_defaults(func=_cmd_sync)

    p = sub.add_parser("integrity", help="Check UI/DB/reference consistency.")
    p.set_defaults(func=_cmd_integrity)

    return parser


def main(argv: list[str] | None = None) -> None:
    configure_utf8_stdio()
    args = build_parser().parse_args(argv)
    result = asyncio.run(args.func(args))
    if isinstance(result, ImportReport):
        _print_report(result)
    else:
        payload = json.dumps(result, indent=2, ensure_ascii=False, default=str)
        sys.stdout.write(payload + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
