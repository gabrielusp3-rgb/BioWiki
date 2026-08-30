from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import OrganismIdPath, api_key_guard, get_session
from app.schemas.organism import OrganismListResponse, OrganismRead
from app.services import mappers, organism_service

router = APIRouter(tags=["organisms"], dependencies=[Depends(api_key_guard)])


@router.get(
    "/organisms/featured",
    response_model=OrganismListResponse,
    summary="Featured organisms (real records only)",
)
async def featured_organisms(
    limit: int = Query(12, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    return await organism_service.featured(session, limit=limit)


@router.get(
    "/organisms", response_model=OrganismListResponse, summary="List organisms"
)
async def list_organisms(
    group: str | None = Query(None, max_length=64, description="Filter by organism group."),
    limit: int = Query(20, ge=1, le=100),
    cursor: str | None = Query(None, max_length=64),
    session: AsyncSession = Depends(get_session),
):
    return await organism_service.list_organisms(
        session, group=group, limit=limit, cursor=cursor
    )


@router.get(
    "/organisms/{identifier}",
    response_model=OrganismRead,
    summary="Get an organism by slug, NCBI tax ID or internal ID",
)
async def get_organism(
    identifier: OrganismIdPath, session: AsyncSession = Depends(get_session)
):
    org = await organism_service.get_by_identifier(session, identifier)
    if org is None:
        raise HTTPException(status_code=404, detail="Organism not found")
    try:
        from app.services import paleogenomics_service

        slugs = await paleogenomics_service.slugs_by_organism_ids(session, [org.id])
    except Exception:
        slugs = {}
    return mappers.to_organism(org, paleogenomic_slug=slugs.get(org.id))
