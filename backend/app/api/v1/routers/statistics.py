from __future__ import annotations

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import api_key_guard, get_session
from app.schemas.statistics import IntegrityReport, StatisticsRead, SyncInfo
from app.services import statistics_service, sync_service

router = APIRouter(tags=["statistics"], dependencies=[Depends(api_key_guard)])


@router.get(
    "/statistics",
    response_model=StatisticsRead,
    summary="Live database statistics (real aggregates, never estimates)",
)
async def get_statistics(
    response: Response, session: AsyncSession = Depends(get_session)
):
    response.headers["Cache-Control"] = "public, max-age=8"
    return await statistics_service.get_statistics(session)


@router.get(
    "/statistics/sync",
    response_model=SyncInfo,
    summary="Synchronisation status: empty | importing | error | updated | connected",
)
async def get_sync_status(session: AsyncSession = Depends(get_session)):
    return await sync_service.get_sync_status(session)


@router.get(
    "/statistics/integrity",
    response_model=IntegrityReport,
    summary="Integrity checks across UI aggregates, stored rows and references",
)
async def get_integrity(session: AsyncSession = Depends(get_session)):
    return await sync_service.check_integrity(session)
