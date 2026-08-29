"""Expand BIOWIKI with real NCBI / UniProt / PDB / Rfam / PubMed records.

Targets are CLI flags, not edited constants:

    sequences  --additional-sequences   (NEW records on top of the current baseline)
    literature --publication-target     (TOTAL unique PubMed catalogue rows)

    python -m scripts.expand_dataset --diversity-plan
    python -m scripts.expand_dataset --dry-run --additional-sequences 10000 --publication-target 25000
    python -m scripts.expand_dataset --validate-only
    python -m scripts.expand_dataset --additional-sequences 10000 --publication-target 25000 --resume
"""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from app.core.stdio import configure_utf8_stdio

configure_utf8_stdio()

from app.pipeline.expansion.checkpoint import DEFAULT_CHECKPOINT_PATH
from app.pipeline.expansion.runner import _source_job_failed, run_expansion, snapshot

__all__ = ["snapshot", "_source_job_failed", "main"]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--additional-sequences",
        type=int,
        default=10000,
        help="NEW biological records to add on top of the current sequence count (default 10000).",
    )
    parser.add_argument(
        "--publication-target",
        type=int,
        default=25000,
        help="TOTAL publication rows to reach, not an additional increment (default 25000).",
    )
    parser.add_argument("--batch-size", type=int, default=200)
    parser.add_argument(
        "--resume",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Resume from the gitignored checkpoint (default true). --no-resume starts a new job.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Discover candidates; do not persist.")
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Snapshot + integrity only; no ingest.",
    )
    parser.add_argument(
        "--source",
        action="append",
        dest="sources",
        help="Repeatable. ncbi, uniprot, rfam, pdb, genomes.",
    )
    parser.add_argument(
        "--category",
        action="append",
        dest="categories",
        help="Repeatable. dna, rna, protein, virus, crispr, genome.",
    )
    parser.add_argument(
        "--diversity-plan",
        action="store_true",
        help="Print the scaled job list and exit.",
    )
    parser.add_argument(
        "--max-record-length",
        type=int,
        default=None,
        help="Optional extra cap on bulk residue length. Overlong records are skipped, never clipped.",
    )
    parser.add_argument("--report", type=Path, default=None, help="Write a JSON summary here.")
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT_PATH)
    parser.add_argument("--sequences-only", action="store_true")
    parser.add_argument("--pubmed-only", action="store_true")
    parser.add_argument(
        "--skip-fill",
        action="store_true",
        help="Deprecated no-op kept so older operator scripts still parse.",
    )
    return parser.parse_args()


async def main() -> None:
    configure_utf8_stdio()
    args = _parse_args()
    await run_expansion(
        additional_sequences=args.additional_sequences,
        publication_target=args.publication_target,
        batch_size=args.batch_size,
        resume=args.resume,
        dry_run=args.dry_run,
        validate_only=args.validate_only,
        sources=set(args.sources) if args.sources else None,
        categories=set(args.categories) if args.categories else None,
        diversity_plan=args.diversity_plan,
        max_record_length=args.max_record_length,
        report_path=args.report,
        sequences_only=args.sequences_only,
        pubmed_only=args.pubmed_only,
        checkpoint_path=args.checkpoint,
    )


if __name__ == "__main__":
    asyncio.run(main())
