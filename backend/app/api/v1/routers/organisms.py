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
    locale: str | None = Query(None, max_length=16),
    session: AsyncSession = Depends(get_session),
):
    from app.pipeline.paleogenomics.vernacular import locale_or_none

    if locale is not None and locale_or_none(locale) is None:
        raise HTTPException(status_code=400, detail="Unsupported locale")
    return await organism_service.featured(session, limit=limit, locale=locale)


@router.get(
    "/organisms", response_model=OrganismListResponse, summary="List organisms"
)
async def list_organisms(
    group: str | None = Query(None, max_length=64, description="Filter by organism group."),
    limit: int = Query(20, ge=1, le=100),
    cursor: str | None = Query(None, max_length=64),
    locale: str | None = Query(None, max_length=16),
    session: AsyncSession = Depends(get_session),
):
    from app.pipeline.paleogenomics.vernacular import locale_or_none

    if locale is not None and locale_or_none(locale) is None:
        raise HTTPException(status_code=400, detail="Unsupported locale")
    return await organism_service.list_organisms(
        session, group=group, limit=limit, cursor=cursor, locale=locale
    )


@router.get(
    "/organisms/{identifier}",
    response_model=OrganismRead,
    summary="Get an organism by slug, NCBI tax ID or internal ID",
)
async def get_organism(
    identifier: OrganismIdPath,
    locale: str | None = Query(None, max_length=16),
    session: AsyncSession = Depends(get_session),
):
    from app.pipeline.paleogenomics.vernacular import locale_or_none
    from app.services.vernacular_service import vernacular_fields

    if locale is not None and locale_or_none(locale) is None:
        raise HTTPException(status_code=400, detail="Unsupported locale")
    org = await organism_service.get_by_identifier(session, identifier)
    if org is None:
        raise HTTPException(status_code=404, detail="Organism not found")
    try:
        from app.services import paleogenomics_service

        slugs = await paleogenomics_service.slugs_by_organism_ids(session, [org.id])
    except Exception:
        slugs = {}
    payload = mappers.to_organism(org, paleogenomic_slug=slugs.get(org.id))
    names = await vernacular_fields(
        session,
        org.id,
        locale=locale,
        english_name=org.common_name,
        scientific_name=org.scientific_name,
    )
    return payload.model_copy(update=names)
