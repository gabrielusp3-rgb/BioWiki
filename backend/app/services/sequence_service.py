"""Query and shape sequence records (DNA, RNA, CRISPR, protein, virus)."""

from __future__ import annotations

from typing import Any

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import defer, noload

from app.models.enums import SequenceType
from app.models.features import (
    CrisprFeature,
    DnaFeature,
    ProteinFeature,
    ProteinPdbRef,
    RnaFeature,
    VirusFeature,
)
from app.models.organism import Organism
from app.models.sequence import Sequence
from app.models.source import DataSource
from app.services import mappers
from app.services.pagination import decode_cursor, encode_cursor

# List endpoints already omit residues in the JSON (`with_residues=False`).
# Deferring the TEXT column and unused selectin relations avoids pulling
# megabases of sequence data and extra round-trips that never reach the client.
_LIST_DEFER = (
    defer(Sequence.residues),
    noload(Sequence.gene),
    noload(Sequence.cross_references),
    noload(Sequence.references),
)
_DNA_LIST_LOAD = _LIST_DEFER + (
    noload(Sequence.rna_feature),
    noload(Sequence.protein_feature),
    noload(Sequence.crispr_feature),
    noload(Sequence.virus_feature),
    noload(Sequence.protein_domains),
    noload(Sequence.pdb_refs),
)
_RNA_LIST_LOAD = _LIST_DEFER + (
    noload(Sequence.dna_feature),
    noload(Sequence.protein_feature),
    noload(Sequence.crispr_feature),
    noload(Sequence.virus_feature),
    noload(Sequence.protein_domains),
    noload(Sequence.pdb_refs),
)
_CRISPR_LIST_LOAD = _LIST_DEFER + (
    noload(Sequence.dna_feature),
    noload(Sequence.rna_feature),
    noload(Sequence.protein_feature),
    noload(Sequence.virus_feature),
    noload(Sequence.protein_domains),
    noload(Sequence.pdb_refs),
)
_PROTEIN_LIST_LOAD = _LIST_DEFER + (
    noload(Sequence.dna_feature),
    noload(Sequence.rna_feature),
    noload(Sequence.crispr_feature),
    noload(Sequence.virus_feature),
)
_VIRUS_LIST_LOAD = _LIST_DEFER + (
    noload(Sequence.dna_feature),
    noload(Sequence.rna_feature),
    noload(Sequence.protein_feature),
    noload(Sequence.crispr_feature),
    noload(Sequence.protein_domains),
    noload(Sequence.pdb_refs),
)


def _apply_text(stmt: Select, q: str | None) -> Select:
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                Sequence.name.ilike(like),
                Sequence.accession.ilike(like),
                Sequence.gene_name.ilike(like),
            )
        )
    return stmt


def _apply_organism(stmt: Select, organism: str | None) -> Select:
    if organism:
        like = f"%{organism.strip()}%"
        stmt = stmt.join(Organism, Sequence.organism_id == Organism.id).where(
            or_(
                Organism.scientific_name.ilike(like),
                Organism.common_name.ilike(like),
                Organism.slug == organism.strip().lower(),
            )
        )
    return stmt


def _apply_source(stmt: Select, source: str | None) -> Select:
    if source:
        stmt = stmt.join(DataSource, Sequence.source_id == DataSource.id).where(
            or_(DataSource.key == source.strip(), DataSource.name.ilike(f"%{source}%"))
        )
    return stmt


def _apply_length(stmt: Select, min_length: int | None, max_length: int | None) -> Select:
    if min_length is not None:
        stmt = stmt.where(Sequence.length >= min_length)
    if max_length is not None:
        stmt = stmt.where(Sequence.length <= max_length)
    return stmt


async def _paginate(
    session: AsyncSession,
    stmt: Select,
    *,
    limit: int,
    cursor: str | None,
    mapper,
    load_options: tuple = (),
) -> dict[str, Any]:
    offset = decode_cursor(cursor)
    count_src = stmt.with_only_columns(
        Sequence.id, maintain_column_froms=True
    ).order_by(None)
    total = int(
        (
            await session.execute(
                select(func.count()).select_from(count_src.subquery())
            )
        ).scalar_one()
    )

    stmt = (
        stmt.options(*load_options)
        .order_by(Sequence.name.asc(), Sequence.id.asc())
        .offset(offset)
        .limit(limit + 1)
    )
    rows = list((await session.execute(stmt)).scalars().unique().all())
    has_more = len(rows) > limit
    rows = rows[:limit]
    next_cursor = encode_cursor(offset + limit) if has_more else None
    return {
        "results": [mapper(r, with_residues=False) for r in rows],
        "total": total,
        "next_cursor": next_cursor,
    }


async def list_dna(session: AsyncSession, **kw: Any) -> dict[str, Any]:
    stmt = select(Sequence).where(Sequence.seq_type == SequenceType.DNA)
    stmt = _apply_text(stmt, kw.get("q"))
    stmt = _apply_organism(stmt, kw.get("organism"))
    stmt = _apply_source(stmt, kw.get("source"))
    stmt = _apply_length(stmt, kw.get("min_length"), kw.get("max_length"))
    if kw.get("molecule_type"):
        stmt = stmt.join(DnaFeature).where(
            DnaFeature.molecule_type == kw["molecule_type"]
        )
    if kw.get("strand"):
        stmt = stmt.join(DnaFeature).where(DnaFeature.strand == kw["strand"])
    return await _paginate(
        session,
        stmt,
        limit=kw["limit"],
        cursor=kw.get("cursor"),
        mapper=mappers.to_dna,
        load_options=_DNA_LIST_LOAD,
    )


async def list_rna(session: AsyncSession, **kw: Any) -> dict[str, Any]:
    stmt = select(Sequence).where(Sequence.seq_type == SequenceType.RNA)
    stmt = _apply_text(stmt, kw.get("q"))
    stmt = _apply_organism(stmt, kw.get("organism"))
    stmt = _apply_source(stmt, kw.get("source"))
    stmt = _apply_length(stmt, kw.get("min_length"), kw.get("max_length"))
    if kw.get("rna_class"):
        stmt = stmt.join(RnaFeature).where(RnaFeature.rna_class == kw["rna_class"])
    if kw.get("coding") is not None:
        stmt = stmt.join(RnaFeature).where(RnaFeature.is_coding == kw["coding"])
    return await _paginate(
        session,
        stmt,
        limit=kw["limit"],
        cursor=kw.get("cursor"),
        mapper=mappers.to_rna,
        load_options=_RNA_LIST_LOAD,
    )


async def list_crispr(session: AsyncSession, **kw: Any) -> dict[str, Any]:
    stmt = select(Sequence).where(Sequence.seq_type == SequenceType.CRISPR)
    stmt = _apply_text(stmt, kw.get("q"))
    stmt = _apply_organism(stmt, kw.get("organism"))
    stmt = _apply_source(stmt, kw.get("source"))
    stmt = _apply_length(stmt, kw.get("min_length"), kw.get("max_length"))
    if kw.get("system"):
        stmt = stmt.join(CrisprFeature).where(CrisprFeature.cas_system == kw["system"])
    if kw.get("target_gene"):
        stmt = stmt.join(CrisprFeature).where(
            CrisprFeature.target_gene.ilike(f"%{kw['target_gene']}%")
        )
    if kw.get("pam"):
        stmt = stmt.join(CrisprFeature).where(CrisprFeature.pam == kw["pam"])
    return await _paginate(
        session,
        stmt,
        limit=kw["limit"],
        cursor=kw.get("cursor"),
        mapper=mappers.to_crispr,
        load_options=_CRISPR_LIST_LOAD,
    )


async def list_proteins(session: AsyncSession, **kw: Any) -> dict[str, Any]:
    stmt = select(Sequence).where(
        Sequence.seq_type.in_([SequenceType.PROTEIN, SequenceType.PEPTIDE])
    )
    stmt = _apply_text(stmt, kw.get("q"))
    stmt = _apply_organism(stmt, kw.get("organism"))
    stmt = _apply_source(stmt, kw.get("source"))
    stmt = _apply_length(stmt, kw.get("min_length"), kw.get("max_length"))
    if kw.get("reviewed") is not None:
        stmt = stmt.join(ProteinFeature).where(
            ProteinFeature.reviewed == kw["reviewed"]
        )
    if kw.get("has_structure"):
        stmt = stmt.where(
            select(ProteinPdbRef.id)
            .where(ProteinPdbRef.sequence_id == Sequence.id)
            .exists()
        )
    return await _paginate(
        session,
        stmt,
        limit=kw["limit"],
        cursor=kw.get("cursor"),
        mapper=mappers.to_protein,
        load_options=_PROTEIN_LIST_LOAD,
    )


async def list_viruses(session: AsyncSession, **kw: Any) -> dict[str, Any]:
    stmt = select(Sequence).where(Sequence.seq_type == SequenceType.VIRUS)
    stmt = _apply_text(stmt, kw.get("q"))
    stmt = _apply_organism(stmt, kw.get("organism"))
    stmt = _apply_source(stmt, kw.get("source"))
    stmt = _apply_length(stmt, kw.get("min_length"), kw.get("max_length"))
    if kw.get("family"):
        stmt = stmt.join(VirusFeature).where(
            VirusFeature.family.ilike(f"%{kw['family']}%")
        )
    if kw.get("host"):
        stmt = stmt.join(VirusFeature).where(VirusFeature.host.ilike(f"%{kw['host']}%"))
    if kw.get("genome_type"):
        stmt = stmt.join(VirusFeature).where(
            VirusFeature.genome_type == kw["genome_type"]
        )
    return await _paginate(
        session,
        stmt,
        limit=kw["limit"],
        cursor=kw.get("cursor"),
        mapper=mappers.to_virus,
        load_options=_VIRUS_LIST_LOAD,
    )


async def get_by_accession(
    session: AsyncSession, accession: str
) -> Sequence | None:
    stmt = select(Sequence).where(Sequence.accession == accession).limit(1)
    return (await session.execute(stmt)).scalars().first()
