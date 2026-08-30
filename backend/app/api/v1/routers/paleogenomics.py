from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import PaleogenomicSlugPath, api_key_guard, get_session
from app.models.enums import ArchaicSource, DeextinctionStatus, ExtinctionStatus, PaleogenomicSubsection
from app.schemas.common import ListResponse
from app.schemas.genome import GenomeRead
from app.schemas.paleogenomics import (
    PaleogenomicIntrogressionList,
    PaleogenomicLanding,
    PaleogenomicOverview,
    PaleogenomicProjectList,
    PaleogenomicSequenceList,
    PaleogenomicSpeciesDetail,
    PaleogenomicSpeciesList,
)
from app.schemas.publication import PublicationRead
from app.services import paleogenomics_service

router = APIRouter(tags=["paleogenomics"], dependencies=[Depends(api_key_guard)])


@router.get("/paleogenomics", response_model=PaleogenomicLanding, summary="Paleogenomics collection")
async def paleogenomics_landing(session: AsyncSession = Depends(get_session)):
    return await paleogenomics_service.landing(session)


@router.get(
    "/paleogenomics/statistics",
    response_model=PaleogenomicOverview,
    summary="Live Paleogenomics counts",
)
async def paleogenomics_statistics(session: AsyncSession = Depends(get_session)):
    return await paleogenomics_service.overview_stats(session)


@router.get(
    "/paleogenomics/species",
    response_model=PaleogenomicSpeciesList,
    summary="List Paleogenomics species profiles",
)
async def list_paleogenomics_species(
    q: str | None = Query(None, max_length=256),
    subsection: PaleogenomicSubsection | None = Query(None),
    extinction_status: ExtinctionStatus | None = Query(None),
    geographic_region: str | None = Query(None, max_length=160),
    deextinction: DeextinctionStatus | None = Query(None),
    dna_available: bool | None = Query(None),
    assembly_available: bool | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    cursor: str | None = Query(None, max_length=64),
    session: AsyncSession = Depends(get_session),
):
    return await paleogenomics_service.list_species(
        session,
        q=q,
        subsection=subsection.value if subsection else None,
        extinction_status=extinction_status.value if extinction_status else None,
        geographic_region=geographic_region,
        deextinction=deextinction.value if deextinction else None,
        dna_available=dna_available,
        assembly_available=assembly_available,
        limit=limit,
        cursor=cursor,
    )


@router.get(
    "/paleogenomics/introgression",
    response_model=PaleogenomicIntrogressionList,
    summary="Archaic introgression in living Homo sapiens",
)
async def list_introgression(
    archaic_source: ArchaicSource | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    cursor: str | None = Query(None, max_length=64),
    session: AsyncSession = Depends(get_session),
):
    return await paleogenomics_service.list_introgression(
        session,
        archaic_source=archaic_source.value if archaic_source else None,
        limit=limit,
        cursor=cursor,
    )


@router.get(
    "/paleogenomics/species/{slug}",
    response_model=PaleogenomicSpeciesDetail,
    summary="Paleogenomics species profile",
)
async def get_paleogenomics_species(slug: PaleogenomicSlugPath, session: AsyncSession = Depends(get_session)):
    detail = await paleogenomics_service.get_species(session, slug)
    if detail is None:
        raise HTTPException(status_code=404, detail="Paleogenomics species not found")
    return detail


@router.get(
    "/paleogenomics/species/{slug}/sequences",
    response_model=PaleogenomicSequenceList,
    summary="Paginated sequences for a Paleogenomics species",
)
async def list_paleogenomics_sequences(
    slug: PaleogenomicSlugPath,
    limit: int = Query(20, ge=1, le=100),
    cursor: str | None = Query(None, max_length=64),
    session: AsyncSession = Depends(get_session),
):
    payload = await paleogenomics_service.list_sequences(session, slug, limit=limit, cursor=cursor)
    if payload is None:
        raise HTTPException(status_code=404, detail="Paleogenomics species not found")
    return payload


@router.get(
    "/paleogenomics/species/{slug}/publications",
    response_model=ListResponse[PublicationRead],
    summary="Paginated publications for a Paleogenomics species",
)
async def list_paleogenomics_publications(
    slug: PaleogenomicSlugPath,
    limit: int = Query(20, ge=1, le=100),
    cursor: str | None = Query(None, max_length=64),
    session: AsyncSession = Depends(get_session),
):
    payload = await paleogenomics_service.list_publications(session, slug, limit=limit, cursor=cursor)
    if payload is None:
        raise HTTPException(status_code=404, detail="Paleogenomics species not found")
    return payload


@router.get(
    "/paleogenomics/species/{slug}/genomes",
    response_model=ListResponse[GenomeRead],
    summary="Paginated genome assemblies for a Paleogenomics species",
)
async def list_paleogenomics_genomes(
    slug: PaleogenomicSlugPath,
    limit: int = Query(20, ge=1, le=100),
    cursor: str | None = Query(None, max_length=64),
    session: AsyncSession = Depends(get_session),
):
    payload = await paleogenomics_service.list_genomes(session, slug, limit=limit, cursor=cursor)
    if payload is None:
        raise HTTPException(status_code=404, detail="Paleogenomics species not found")
    return payload


@router.get(
    "/paleogenomics/species/{slug}/projects",
    response_model=PaleogenomicProjectList,
    summary="BioProject/BioSample metadata (not raw SRA reads)",
)
async def list_paleogenomics_projects(
    slug: PaleogenomicSlugPath,
    limit: int = Query(20, ge=1, le=100),
    cursor: str | None = Query(None, max_length=64),
    session: AsyncSession = Depends(get_session),
):
    payload = await paleogenomics_service.list_projects(session, slug, limit=limit, cursor=cursor)
    if payload is None:
        raise HTTPException(status_code=404, detail="Paleogenomics species not found")
    return payload
