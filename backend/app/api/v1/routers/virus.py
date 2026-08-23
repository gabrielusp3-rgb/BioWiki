from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AccessionPath, api_key_guard, get_session
from app.models.enums import SequenceType
from app.schemas.common import ListResponse
from app.schemas.sequence import VirusRead
from app.services import mappers, sequence_service

router = APIRouter(tags=["virus"], dependencies=[Depends(api_key_guard)])


@router.get("/viruses", response_model=ListResponse[VirusRead], summary="List viruses")
async def list_virus(
    q: str | None = Query(None, max_length=256, description="Free-text query over name/accession."),
    family: str | None = Query(None, max_length=128),
    host: str | None = Query(None, max_length=256),
    source: str | None = Query(None, max_length=64),
    genome_type: str | None = Query(None, max_length=64),
    organism: str | None = Query(None, max_length=256),
    min_length: int | None = Query(None, ge=0),
    max_length: int | None = Query(None, ge=0),
    limit: int = Query(20, ge=1, le=100),
    cursor: str | None = Query(None, max_length=64),
    session: AsyncSession = Depends(get_session),
):
    return await sequence_service.list_viruses(
        session, q=q, family=family, host=host, source=source,
        genome_type=genome_type, organism=organism, min_length=min_length,
        max_length=max_length, limit=limit, cursor=cursor,
    )


@router.get(
    "/viruses/{accession}",
    response_model=VirusRead,
    summary="Get a single virus by accession (with residues)",
)
async def get_virus(accession: AccessionPath, session: AsyncSession = Depends(get_session)):
    seq = await sequence_service.get_by_accession(session, accession)
    if seq is None or seq.seq_type != SequenceType.VIRUS:
        raise HTTPException(status_code=404, detail="Virus not found")
    return mappers.to_virus(seq, with_residues=True)
