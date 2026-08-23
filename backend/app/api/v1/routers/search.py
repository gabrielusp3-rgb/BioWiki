from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import api_key_guard, get_session
from app.schemas.search import SearchResponse, SuggestResponse
from app.services import search_service

router = APIRouter(tags=["search"], dependencies=[Depends(api_key_guard)])


@router.get(
    "/search", response_model=SearchResponse, summary="Full-text search across all sequences"
)
async def search(
    q: str = Query(..., min_length=1, max_length=256, description="Search query (websearch syntax)."),
    types: str | None = Query(None, max_length=128, description="Comma-separated sequence types."),
    organism: str | None = Query(None, max_length=256),
    source: str | None = Query(None, max_length=64),
    category: str | None = Query(None, max_length=64),
    min_length: int | None = Query(None, ge=0),
    max_length: int | None = Query(None, ge=0),
    complexity: str | None = Query(None, max_length=16, description="low | medium | high"),
    limit: int = Query(20, ge=1, le=100),
    cursor: str | None = Query(None, max_length=64),
    session: AsyncSession = Depends(get_session),
):
    return await search_service.search(
        session, q=q, types=types, organism=organism, source=source,
        category=category, min_length=min_length, max_length=max_length,
        complexity=complexity, limit=limit, cursor=cursor,
    )


@router.get(
    "/search/suggest", response_model=SuggestResponse, summary="Autocomplete suggestions"
)
async def suggest(
    q: str = Query(..., min_length=1, max_length=256),
    limit: int = Query(8, ge=1, le=25),
    session: AsyncSession = Depends(get_session),
):
    return await search_service.suggest(session, q=q, limit=limit)
