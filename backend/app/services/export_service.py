"""Serialise real sequence records to FASTA, CSV, JSON and GenBank."""

from __future__ import annotations

import csv
import io
import json
import re
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import SequenceType
from app.models.organism import Organism
from app.models.sequence import Sequence
from app.models.source import DataSource


_FILENAME_SAFE = re.compile(r"[^A-Za-z0-9._-]+")


def safe_download_filename(stem: str, suffix: str) -> str:
    """Build a Content-Disposition filename without quotes or path/CRLF."""
    cleaned = _FILENAME_SAFE.sub("_", (stem or "").strip())[:64].strip("._") or "sequence"
    ext = suffix if suffix.startswith(".") else f".{suffix}"
    return f"{cleaned}{ext}"


def _wrap(seq: str, width: int = 70) -> str:
    return "\n".join(seq[i : i + width] for i in range(0, len(seq), width))


def _organism(seq: Sequence) -> str:
    return seq.organism.scientific_name if seq.organism else ""


def _to_fasta(rows: list[Sequence]) -> str:
    parts = []
    for s in rows:
        header = f">{s.accession} {s.name} [{_organism(s)}]"
        body = _wrap(s.residues or "")
        parts.append(f"{header}\n{body}")
    return "\n".join(parts) + ("\n" if parts else "")


def _to_csv(rows: list[Sequence]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        ["accession", "name", "type", "organism", "source", "length", "gene_name"]
    )
    for s in rows:
        writer.writerow(
            [
                s.accession,
                s.name,
                s.seq_type.value,
                _organism(s),
                s.source.name if s.source else "",
                s.length,
                s.gene_name or "",
            ]
        )
    return buf.getvalue()


def _to_json(rows: list[Sequence]) -> str:
    data: list[dict[str, Any]] = [
        {
            "accession": s.accession,
            "name": s.name,
            "type": s.seq_type.value,
            "organism": _organism(s),
            "taxId": s.organism.tax_id if s.organism else None,
            "source": s.source.name if s.source else "",
            "length": s.length,
            "geneName": s.gene_name,
            "sequence": s.residues,
        }
        for s in rows
    ]
    return json.dumps(data, indent=2, ensure_ascii=False)


def _to_genbank(s: Sequence) -> str:
    lines = [
        f"LOCUS       {s.accession:<16} {s.length} bp    {(s.molecule.value if s.molecule else 'DNA').upper()}",
        f"DEFINITION  {s.name}.",
        f"ACCESSION   {s.accession}",
        f"VERSION     {s.accession}.{s.version or '1'}",
        f"SOURCE      {_organism(s)}",
        f"  ORGANISM  {_organism(s)}",
        "ORIGIN",
    ]
    residues = (s.residues or "").lower()
    for i in range(0, len(residues), 60):
        chunk = residues[i : i + 60]
        blocks = " ".join(chunk[j : j + 10] for j in range(0, len(chunk), 10))
        lines.append(f"{i + 1:>9} {blocks}")
    lines.append("//")
    return "\n".join(lines) + "\n"


async def _query_rows(
    session: AsyncSession,
    *,
    type: str | None,
    q: str | None,
    organism: str | None,
    source: str | None,
    gene: str | None,
    limit: int,
) -> list[Sequence]:
    stmt = select(Sequence)
    if type:
        try:
            stmt = stmt.where(Sequence.seq_type == SequenceType(type))
        except ValueError:
            pass
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(Sequence.name.ilike(like), Sequence.accession.ilike(like))
        )
    if gene:
        stmt = stmt.where(Sequence.gene_name.ilike(f"%{gene.strip()}%"))
    if organism:
        olike = f"%{organism.strip()}%"
        stmt = stmt.join(Organism, Sequence.organism_id == Organism.id).where(
            or_(
                Organism.scientific_name.ilike(olike),
                Organism.common_name.ilike(olike),
            )
        )
    if source:
        stmt = stmt.join(DataSource, Sequence.source_id == DataSource.id).where(
            DataSource.key == source.strip()
        )
    stmt = stmt.order_by(Sequence.accession.asc()).limit(limit)
    return list((await session.execute(stmt)).scalars().unique().all())


async def export_sequences(
    session: AsyncSession, *, format: str, limit: int, **filters: Any
) -> tuple[str, str, str]:
    rows = await _query_rows(session, limit=limit, **filters)
    fmt = (format or "fasta").lower()
    if fmt == "csv":
        return _to_csv(rows), "text/csv", safe_download_filename("biowiki_sequences", ".csv")
    if fmt == "json":
        return _to_json(rows), "application/json", safe_download_filename("biowiki_sequences", ".json")
    return _to_fasta(rows), "text/plain", safe_download_filename("biowiki_sequences", ".fasta")


async def export_single(
    session: AsyncSession, *, accession: str, format: str
) -> tuple[str, str, str] | None:
    seq = (
        await session.execute(
            select(Sequence).where(Sequence.accession == accession).limit(1)
        )
    ).scalars().first()
    if seq is None:
        return None
    fmt = (format or "fasta").lower()
    if fmt == "genbank":
        return _to_genbank(seq), "text/plain", safe_download_filename(accession, ".gb")
    if fmt == "json":
        return _to_json([seq]), "application/json", safe_download_filename(accession, ".json")
    return _to_fasta([seq]), "text/plain", safe_download_filename(accession, ".fasta")
