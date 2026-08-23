"""Backfill empty ``sequences.residues`` from official NCBI FASTA / gbwithparts.

Surgical and idempotent:
- only rows with NULL/empty residues are candidates;
- only ``residues``, ``checksum`` and ``gc_content`` are updated;
- accession, organism, gene, name, publications and length are left untouched;
- a length mismatch against the stored LOCUS length is reported, not forced;
- residues are never invented.

Run from ``backend/`` with the virtualenv active:

    python -m scripts.backfill_empty_residues --dry-run
    python -m scripts.backfill_empty_residues
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
from dataclasses import dataclass, field

from sqlalchemy import or_, select

from app.database.session import get_sessionmaker
from app.models.sequence import Sequence
from app.pipeline.fetchers.ncbi import fetch_official_residues, lookup_fasta_residues
from app.pipeline.logging import get_logger
from app.pipeline.validation import _NUCLEOTIDE, _PROTEIN, compute_gc

logger = get_logger("biowiki.pipeline.backfill")

_REPRESENTATIVE = ("NG_074726", "NG_047936", "NG_048025")


@dataclass
class BackfillReport:
    identified: list[str] = field(default_factory=list)
    recovered: list[str] = field(default_factory=list)
    skipped_already_filled: int = 0
    diverged: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "identified": len(self.identified),
            "recovered": len(self.recovered),
            "skipped_already_filled": self.skipped_already_filled,
            "diverged": len(self.diverged),
            "failed": len(self.failed),
            "failed_accessions": list(self.failed),
            "diverged_accessions": list(self.diverged),
            "errors": list(self.errors),
        }


def _alphabet_for(seq_type: str) -> set[str]:
    if seq_type in {"protein", "peptide"}:
        return _PROTEIN
    return _NUCLEOTIDE


def _entrez_db(seq_type: str) -> str:
    return "protein" if seq_type in {"protein", "peptide"} else "nuccore"


async def backfill_empty_residues(*, dry_run: bool = False) -> BackfillReport:
    report = BackfillReport()
    session_factory = get_sessionmaker()

    async with session_factory() as session:
        rows = list(
            (
                await session.execute(
                    select(Sequence)
                    .where(or_(Sequence.residues.is_(None), Sequence.residues == ""))
                    .order_by(Sequence.accession)
                )
            )
            .scalars()
            .all()
        )
        report.identified = [row.accession for row in rows]
        if not rows:
            logger.info("Backfill completed: no empty residues")
            return report

        by_db: dict[str, list[Sequence]] = {}
        for row in rows:
            by_db.setdefault(_entrez_db(row.seq_type.value), []).append(row)

        mapping: dict[str, str] = {}
        for db, group in by_db.items():
            ids = [
                f"{row.accession}.{row.version}" if row.version else row.accession
                for row in group
            ]
            mapping.update(await fetch_official_residues(ids, db=db))

        for row in rows:
            residues = lookup_fasta_residues(mapping, row.accession, row.version)
            if not residues:
                msg = (
                    f"{row.accession}: NCBI returned no recoverable FASTA/gbwithparts sequence"
                )
                report.failed.append(row.accession)
                report.errors.append(msg)
                logger.warning(msg)
                continue

            cleaned = "".join(ch for ch in residues if not ch.isspace()).upper()
            invalid = set(cleaned) - _alphabet_for(row.seq_type.value)
            if invalid:
                msg = f"{row.accession}: official residues have invalid symbols {sorted(invalid)}"
                report.failed.append(row.accession)
                report.errors.append(msg)
                logger.warning(msg)
                continue

            stored_len = int(row.length)
            if stored_len > 0 and len(cleaned) != stored_len:
                msg = (
                    f"{row.accession}: length mismatch stored={stored_len} "
                    f"official={len(cleaned)}; residues not forced"
                )
                report.diverged.append(row.accession)
                report.errors.append(msg)
                logger.warning(msg)
                continue

            digest = hashlib.sha256(cleaned.encode("ascii", "ignore")).hexdigest()
            gc_value = (
                compute_gc(cleaned)
                if row.seq_type.value not in {"protein", "peptide"}
                else None
            )

            if dry_run:
                report.recovered.append(row.accession)
                logger.info(
                    "dry-run would persist %s (%d residues)",
                    row.accession,
                    len(cleaned),
                )
                continue

            async with session.begin_nested():
                row.residues = cleaned
                row.checksum = digest
                row.gc_content = gc_value
            report.recovered.append(row.accession)
            logger.info("Sequence persisted %s (%d residues)", row.accession, len(cleaned))

        if not dry_run:
            await session.commit()

    logger.info("Backfill completed: %s", report.as_dict())
    return report


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch and validate but do not write to the database.",
    )
    return parser.parse_args()


async def _amain() -> int:
    args = _parse_args()
    report = await backfill_empty_residues(dry_run=args.dry_run)
    print("identified", len(report.identified))
    print("recovered", len(report.recovered))
    print("diverged", len(report.diverged), report.diverged)
    print("failed", len(report.failed), report.failed)
    for acc in _REPRESENTATIVE:
        status = "recovered" if acc in report.recovered else (
            "identified" if acc in report.identified else "not-in-empty-set"
        )
        print(f"representative {acc}: {status}")
    return 1 if report.failed or report.diverged else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_amain()))
