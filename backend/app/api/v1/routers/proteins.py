from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AccessionPath, api_key_guard, get_session
from app.models.enums import SequenceType
from app.schemas.common import ListResponse
from app.schemas.sequence import ProteinRead
from app.services import mappers, sequence_service

router = APIRouter(tags=["proteins"], dependencies=[Depends(api_key_guard)])


@router.get("/proteins", response_model=ListResponse[ProteinRead], summary="List proteins")
async def list_proteins(
    q: str | None = Query(None, max_length=256, description="Free-text query over name/accession."),
    organism: str | None = Query(None, max_length=256),
    source: str | None = Query(None, max_length=64),
    reviewed: bool | None = Query(None),
    has_structure: bool | None = Query(None),
    min_length: int | None = Query(None, ge=0),
    max_length: int | None = Query(None, ge=0),
    limit: int = Query(20, ge=1, le=100),
    cursor: str | None = Query(None, max_length=64),
    session: AsyncSession = Depends(get_session),
):
    return await sequence_service.list_proteins(
        session, q=q, organism=organism, source=source, reviewed=reviewed,
        has_structure=has_structure, min_length=min_length, max_length=max_length,
        limit=limit, cursor=cursor,
    )


@router.get(
    "/proteins/{accession}",
    response_model=ProteinRead,
    summary="Get a single protein by accession (with residues)",
)
async def get_protein(accession: AccessionPath, session: AsyncSession = Depends(get_session)):
    seq = await sequence_service.get_by_accession(session, accession)
    if seq is None or seq.seq_type not in (SequenceType.PROTEIN, SequenceType.PEPTIDE):
        raise HTTPException(status_code=404, detail="Protein not found")
    return mappers.to_protein(seq, with_residues=True)
