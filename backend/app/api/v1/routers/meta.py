from __future__ import annotations

import logging
from time import monotonic

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session

logger = logging.getLogger("biowiki.api")

router = APIRouter(tags=["meta"])

_READY_TTL_SECONDS = 5.0
_ready_cached_at = 0.0
_ready_payload: dict[str, str] | None = None


@router.get("/health", summary="Liveness probe")
async def health() -> dict:
    return {"status": "ok"}


@router.get("/ready", summary="Readiness probe (checks the database)")
async def ready(session: AsyncSession = Depends(get_session)) -> dict:
    global _ready_cached_at, _ready_payload
    now = monotonic()
    if _ready_payload is not None and (now - _ready_cached_at) < _READY_TTL_SECONDS:
        return _ready_payload
    try:
        await session.execute(text("SELECT 1"))
        payload: dict[str, str] = {"status": "ready", "database": "up"}
    except Exception:
        logger.exception("readiness check failed")
        payload = {"status": "degraded", "database": "down"}
    _ready_cached_at = now
    _ready_payload = payload
    return payload
