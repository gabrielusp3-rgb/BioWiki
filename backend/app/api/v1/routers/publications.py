from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import api_key_guard, get_session
from app.schemas.common import ListResponse
from app.schemas.publication import PublicationDetail, PublicationRead
from app.services import mappers, publication_service

router = APIRouter(tags=["publications"], dependencies=[Depends(api_key_guard)])


@router.get(
    "/publications",
    response_model=ListResponse[PublicationRead],
    summary="List scientific publications",
)
async def list_publications(
    q: str | None = Query(None, max_length=256, description="Free text over title/abstract."),
    accession: str | None = Query(
        None, max_length=64, description="Only publications linked to this sequence accession."
    ),
    gene: str | None = Query(
        None, max_length=120, description="Only publications linked to sequences of this gene symbol."
    ),
    organism: str | None = Query(
        None, max_length=256, description="Only publications linked to sequences of this organism."
    ),
    year: int | None = Query(None, ge=1800, le=2100),
    limit: int = Query(20, ge=1, le=100),
    cursor: str | None = Query(None, max_length=64),
    session: AsyncSession = Depends(get_session),
):
    return await publication_service.list_publications(
        session, q=q, accession=accession, gene=gene, organism=organism,
        year=year, limit=limit, cursor=cursor,
    )


@router.get(
    "/publications/{pubmed_id}",
    response_model=PublicationDetail,
    summary="Get a publication by PubMed ID (with linked sequence accessions)",
)
async def get_publication(
    pubmed_id: int = Path(..., ge=1, le=2_147_483_647),
    session: AsyncSession = Depends(get_session),
):
    pub, accessions = await publication_service.get_by_pubmed_id(session, pubmed_id)
    if pub is None:
        raise HTTPException(status_code=404, detail="Publication not found")
    return mappers.to_publication_detail(pub, accessions)
