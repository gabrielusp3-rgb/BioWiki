"""Manual CLI entrypoint for running an import job.

This does NOT run automatically. Invoke it explicitly, e.g.:

    python -m app.pipeline.workers.runner \\
        --file data/refseq_dna.fasta --format fasta \\
        --source-key refseq --source-name "NCBI RefSeq" \\
        --seq-type dna --molecule dna \\
        --organism "Homo sapiens" --tax-id 9606 --group animal

For FASTA/CSV without embedded organism data, provide the organism via flags so
the pipeline persists real provenance (it never invents it).
"""

from __future__ import annotations

import argparse
import asyncio

from app.pipeline.logging import get_logger
from app.pipeline.models import ImportContext, ParsedOrganism
from app.pipeline.workers.import_worker import import_file

logger = get_logger("biowiki.pipeline.runner")


def _build_context(args: argparse.Namespace) -> ImportContext:
    organism = None
    if args.organism and args.tax_id:
        organism = ParsedOrganism(
            scientific_name=args.organism,
            tax_id=args.tax_id,
            common_name=args.common_name,
            group=args.group,
        )
    return ImportContext(
        source_key=args.source_key,
        source_name=args.source_name,
        seq_type=args.seq_type,
        molecule=args.molecule,
        organism=organism,
    )


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="BIOWIKI data import runner.")
    parser.add_argument("--file", required=True, help="Path to the source document.")
    parser.add_argument("--format", dest="fmt", default=None, help="fasta|genbank|json|csv")
    parser.add_argument("--source-key", required=True, help="Data source key, e.g. refseq.")
    parser.add_argument("--source-name", default=None, help="Human-readable source name.")
    parser.add_argument("--seq-type", default=None, help="dna|rna|protein|crispr|virus|genome")
    parser.add_argument("--molecule", default=None, help="dna|rna|protein")
    parser.add_argument("--organism", default=None, help="Default organism scientific name.")
    parser.add_argument("--tax-id", type=int, default=None, help="Default organism NCBI tax id.")
    parser.add_argument("--common-name", default=None)
    parser.add_argument("--group", default=None, help="animal|plant|fungus|bacteria|archaea|virus|protozoan")
    parser.add_argument("--batch-size", type=int, default=200)
    return parser.parse_args(argv)


async def _run(args: argparse.Namespace) -> None:
    context = _build_context(args)
    report = await import_file(
        args.file, context, fmt=args.fmt, batch_size=args.batch_size
    )
    logger.info("Report: %s", report.as_dict())


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    asyncio.run(_run(args))


if __name__ == "__main__":
    main()
