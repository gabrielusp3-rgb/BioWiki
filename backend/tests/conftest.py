"""Shared pytest fixtures. Production data is read-only from these tests."""

from __future__ import annotations

import pytest
import httpx

API_ROOT = "http://127.0.0.1:8000"
API_BASE = f"{API_ROOT}/api/v1"


@pytest.fixture(scope="session")
def api() -> httpx.Client:
    client = httpx.Client(base_url=API_BASE, timeout=60.0, follow_redirects=True)
    try:
        response = client.get("/health")
    except httpx.RequestError as exc:
        client.close()
        pytest.fail(f"BIOWIKI API is not reachable at {API_BASE}: {exc}")
    if response.status_code != 200:
        client.close()
        pytest.fail(f"BIOWIKI /health returned {response.status_code}")
    yield client
    client.close()


@pytest.fixture(scope="session")
def api_root() -> httpx.Client:
    client = httpx.Client(base_url=API_ROOT, timeout=60.0, follow_redirects=True)
    yield client
    client.close()


@pytest.fixture(scope="session", autouse=True)
async def _dispose_engine():
    yield
    from app.database.session import get_engine, get_sessionmaker

    await get_engine().dispose()
    get_engine.cache_clear()
    get_sessionmaker.cache_clear()
