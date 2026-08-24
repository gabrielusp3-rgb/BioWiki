"""Async engine and session management."""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from functools import lru_cache

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.core.config import get_settings


@lru_cache
def get_engine() -> AsyncEngine:
    settings = get_settings()
    connect_args: dict = {}
    use_ssl = settings.database_ssl or settings.is_production
    if use_ssl and "ssl=" not in settings.database_url:
        connect_args["ssl"] = True
    kwargs: dict = {
        "echo": settings.sql_echo,
        "connect_args": connect_args,
        "pool_pre_ping": True,
    }
    # Serverless (Vercel Fluid) should not keep a process-wide connection pool.
    if os.environ.get("VERCEL"):
        kwargs["poolclass"] = NullPool
    else:
        kwargs["pool_size"] = settings.db_pool_size
        kwargs["max_overflow"] = settings.db_max_overflow
        kwargs["pool_recycle"] = 1800
    return create_async_engine(settings.database_url, **kwargs)


@lru_cache
def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind=get_engine(), expire_on_commit=False, class_=AsyncSession
    )


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with get_sessionmaker()() as session:
        yield session
