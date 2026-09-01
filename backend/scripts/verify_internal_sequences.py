"""Read-only internal residue/identity audit. Never writes. No secret output.

Compares stored residues against stored length and SHA-256 checksum for every
Sequence row. External NCBI/UniProt comparison is a separate checkpointed job.

Run:
  python scripts/with_production_env.py python scripts/verify_internal_sequences.py
"""

from __future__ import annotations

import asyncio
import hashlib
import json
from collections import Counter, defaultdict

from sqlalchemy import func, select

from app.database.session import get_sessionmaker
from app.models.enums import SequenceType
from app.models.sequence import Sequence

_NUCLEOTIDE = set("ACGTUNRYSWKMBDHV-")
_PROTEIN = set("ACDEFGHIKLMNPQRSTVWYBXZJUO*-")


def _alphabet(seq: str) -> str:
    letters = {ch for ch in seq.upper() if ch.isalpha() or ch in "*-"}
    if not letters:
        return "empty"
    if letters <= _NUCLEOTIDE:
        return "nucleotide"
    if letters <= _PROTEIN:
        return "protein"
    if letters <= (_NUCLEOTIDE | _PROTEIN):
        return "mixed"
    return "invalid"


async def main() -> None:
    report: dict = {
        "total": 0,
        "missing_residues": 0,
        "empty_residues": 0,
        "length_mismatch": 0,
        "checksum_mismatch": 0,
        "missing_checksum": 0,
        "invalid_alphabet": 0,
        "by_type": {},
        "length_mismatch_accessions": [],
        "checksum_mismatch_accessions": [],
        "invalid_alphabet_accessions": [],
        "checksum_clusters": 0,
    }
    clusters: dict[str, list[str]] = defaultdict(list)

    async with get_sessionmaker()() as session:
        total = int((await session.execute(select(func.count()).select_from(Sequence))).scalar_one())
        report["total"] = total
        offset = 0
        batch = 500
        while offset < total:
            rows = list(
                (
                    await session.execute(
                        select(
                            Sequence.id,
                            Sequence.accession,
                            Sequence.version,
                            Sequence.seq_type,
                            Sequence.length,
                            Sequence.residues,
                            Sequence.checksum,
                        )
                        .order_by(Sequence.accession)
                        .offset(offset)
                        .limit(batch)
                    )
                ).all()
            )
            if not rows:
                break
            for _id, accession, version, seq_type, length, residues, checksum in rows:
                key = seq_type.value if hasattr(seq_type, "value") else str(seq_type)
                bucket = report["by_type"].setdefault(
                    key,
                    {
                        "n": 0,
                        "missing_residues": 0,
                        "length_mismatch": 0,
                        "checksum_mismatch": 0,
                    },
                )
                bucket["n"] += 1
                acc = f"{accession}.{version}" if version else accession
                if residues is None:
                    report["missing_residues"] += 1
                    bucket["missing_residues"] += 1
                    continue
                if residues == "":
                    report["empty_residues"] += 1
                    continue
                if length is not None and len(residues) != int(length):
                    report["length_mismatch"] += 1
                    bucket["length_mismatch"] += 1
                    if len(report["length_mismatch_accessions"]) < 25:
                        report["length_mismatch_accessions"].append(acc)
                digest = hashlib.sha256(residues.encode("ascii", "ignore")).hexdigest()
                clusters[digest].append(acc)
                if not checksum:
                    report["missing_checksum"] += 1
                elif checksum != digest:
                    report["checksum_mismatch"] += 1
                    bucket["checksum_mismatch"] += 1
                    if len(report["checksum_mismatch_accessions"]) < 25:
                        report["checksum_mismatch_accessions"].append(acc)
                kind = _alphabet(residues)
                nucleotide_types = {
                    SequenceType.DNA,
                    SequenceType.RNA,
                    SequenceType.CRISPR,
                    SequenceType.VIRUS,
                }
                if seq_type in nucleotide_types and kind in {"protein", "invalid"}:
                    report["invalid_alphabet"] += 1
                    if len(report["invalid_alphabet_accessions"]) < 25:
                        report["invalid_alphabet_accessions"].append(
                            {"accession": acc, "type": key, "alphabet": kind}
                        )
                if seq_type in {SequenceType.PROTEIN, SequenceType.PEPTIDE} and kind in {
                    "nucleotide",
                    "invalid",
                }:
                    report["invalid_alphabet"] += 1
                    if len(report["invalid_alphabet_accessions"]) < 25:
                        report["invalid_alphabet_accessions"].append(
                            {"accession": acc, "type": key, "alphabet": kind}
                        )
            offset += len(rows)

    report["checksum_clusters"] = sum(1 for members in clusters.values() if len(members) > 1)
    print(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(main())
