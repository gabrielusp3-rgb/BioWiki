from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AccessionPath, api_key_guard, get_session
from app.schemas.common import ListResponse
from app.schemas.sequence import CrisprRead, RnaRead
from app.services import mappers, sequence_service

router = APIRouter(tags=["sequences"], dependencies=[Depends(api_key_guard)])

_LIMIT = Query(20, ge=1, le=100, description="Maximum number of records to return (1–100).")
_CURSOR = Query(
    None,
    max_length=64,
    description="Opaque keyset token from a previous response's nextCursor field.",
)
_Q = Query(None, max_length=256, description="Free-text query over name/accession.")
_ORGANISM = Query(None, max_length=256)
_SOURCE = Query(None, max_length=64)
_SHORT = Query(None, max_length=64)
_GENE = Query(None, max_length=120)


@router.get("/sequences", summary="List nucleotide sequences (DNA, RNA or CRISPR)")
async def list_sequences(
    type: str = Query(..., max_length=16, description="Sequence type: dna | rna | crispr"),
    q: str | None = _Q,
    organism: str | None = _ORGANISM,
    source: str | None = _SOURCE,
    molecule_type: str | None = _SHORT,
    strand: str | None = _SHORT,
    rna_class: str | None = _SHORT,
    coding: bool | None = Query(None),
    system: str | None = _SHORT,
    target_gene: str | None = _GENE,
    pam: str | None = _SHORT,
    min_length: int | None = Query(None, ge=0),
    max_length: int | None = Query(None, ge=0),
    limit: int = _LIMIT,
    cursor: str | None = _CURSOR,
    session: AsyncSession = Depends(get_session),
):
    kw = dict(
        q=q, organism=organism, source=source, min_length=min_length,
        max_length=max_length, limit=limit, cursor=cursor,
    )
    t = type.lower()
    if t == "dna":
        return await sequence_service.list_dna(
            session, molecule_type=molecule_type, strand=strand, **kw
        )
    if t == "rna":
        return await sequence_service.list_rna(
            session, rna_class=rna_class, coding=coding, **kw
        )
    if t == "crispr":
        return await sequence_service.list_crispr(
            session, system=system, target_gene=target_gene, pam=pam, **kw
        )
    raise HTTPException(status_code=422, detail="type must be dna, rna or crispr")


@router.get("/rna", response_model=ListResponse[RnaRead], summary="List RNA sequences")
async def list_rna(
    q: str | None = _Q,
    organism: str | None = _ORGANISM,
    source: str | None = _SOURCE,
    rna_class: str | None = _SHORT,
    coding: bool | None = Query(None),
    min_length: int | None = Query(None, ge=0),
    max_length: int | None = Query(None, ge=0),
    limit: int = _LIMIT,
    cursor: str | None = _CURSOR,
    session: AsyncSession = Depends(get_session),
):
    return await sequence_service.list_rna(
        session, q=q, organism=organism, source=source, rna_class=rna_class,
        coding=coding, min_length=min_length, max_length=max_length,
        limit=limit, cursor=cursor,
    )


@router.get(
    "/crispr", response_model=ListResponse[CrisprRead], summary="List CRISPR guide sequences"
)
async def list_crispr(
    q: str | None = _Q,
    organism: str | None = _ORGANISM,
    source: str | None = _SOURCE,
    system: str | None = _SHORT,
    target_gene: str | None = _GENE,
    pam: str | None = _SHORT,
    min_length: int | None = Query(None, ge=0),
    max_length: int | None = Query(None, ge=0),
    limit: int = _LIMIT,
    cursor: str | None = _CURSOR,
    session: AsyncSession = Depends(get_session),
):
    return await sequence_service.list_crispr(
        session, q=q, organism=organism, source=source, system=system,
        target_gene=target_gene, pam=pam, min_length=min_length,
        max_length=max_length, limit=limit, cursor=cursor,
    )


@router.get(
    "/sequences/{accession}", summary="Get a single sequence by accession (with residues)"
)
async def get_sequence(
    accession: AccessionPath, session: AsyncSession = Depends(get_session)
):
    seq = await sequence_service.get_by_accession(session, accession)
    if seq is None:
        raise HTTPException(status_code=404, detail="Sequence not found")
    return mappers.to_sequence(seq, with_residues=True)
