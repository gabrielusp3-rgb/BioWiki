from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AccessionPath, api_key_guard, get_session
from app.schemas.common import ListResponse
from app.schemas.genome import GenomeRead
from app.services import genome_service, mappers

router = APIRouter(tags=["genomes"], dependencies=[Depends(api_key_guard)])


@router.get(
    "/genomes", response_model=ListResponse[GenomeRead], summary="List genome assemblies"
)
async def list_genomes(
    q: str | None = Query(None, max_length=256, description="Free text over accession/name/description."),
    organism: str | None = Query(None, max_length=256, description="Scientific or common organism name."),
    assembly_level: str | None = Query(
        None, max_length=32, description="complete | chromosome | scaffold | contig"
    ),
    source: str | None = Query(None, max_length=64, description="Source database key."),
    limit: int = Query(20, ge=1, le=100),
    cursor: str | None = Query(None, max_length=64),
    session: AsyncSession = Depends(get_session),
):
    return await genome_service.list_genomes(
        session, q=q, organism=organism, assembly_level=assembly_level,
        source=source, limit=limit, cursor=cursor,
    )


@router.get(
    "/genomes/{accession}",
    response_model=GenomeRead,
    summary="Get a genome assembly by accession",
)
async def get_genome(accession: AccessionPath, session: AsyncSession = Depends(get_session)):
    g = await genome_service.get_by_accession(session, accession)
    if g is None:
        raise HTTPException(status_code=404, detail="Genome not found")
    return mappers.to_genome(g)
