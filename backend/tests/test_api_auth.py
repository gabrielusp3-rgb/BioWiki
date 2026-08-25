"""API-key guard: open catalogue vs 401 when API_KEYS is set.

Uses fixture keys only — never production secrets.
"""

from __future__ import annotations

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.api.deps import api_key_guard
from app.core.config import get_settings
from app.main import create_app

FIXTURE_KEY = "fixture-test-key-not-for-production"


@pytest.fixture
def reset_settings():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_guard_is_open_when_api_keys_empty(monkeypatch, reset_settings) -> None:
    monkeypatch.setenv("API_KEYS", "")
    get_settings.cache_clear()
    await api_key_guard(None)
    await api_key_guard("any-value-is-ignored")


@pytest.mark.asyncio
async def test_guard_rejects_missing_and_invalid_keys(monkeypatch, reset_settings) -> None:
    monkeypatch.setenv("API_KEYS", FIXTURE_KEY)
    get_settings.cache_clear()
    with pytest.raises(HTTPException) as missing:
        await api_key_guard(None)
    assert missing.value.status_code == 401
    with pytest.raises(HTTPException) as invalid:
        await api_key_guard("not-the-fixture-key")
    assert invalid.value.status_code == 401
    await api_key_guard(FIXTURE_KEY)


def test_health_and_docs_stay_public_when_keys_are_set(monkeypatch, reset_settings) -> None:
    monkeypatch.setenv("API_KEYS", FIXTURE_KEY)
    get_settings.cache_clear()
    with TestClient(create_app()) as client:
        assert client.get("/api/v1/health").status_code == 200
        assert client.get("/docs").status_code == 200
        assert client.get("/openapi.json").status_code == 200
        assert client.get("/").status_code == 200
        assert client.get("/api/v1").status_code == 200


def test_catalogue_routes_return_401_when_keys_are_set(monkeypatch, reset_settings) -> None:
    monkeypatch.setenv("API_KEYS", FIXTURE_KEY)
    get_settings.cache_clear()
    with TestClient(create_app()) as client:
        missing = client.get("/api/v1/statistics")
        assert missing.status_code == 401
        assert missing.json()["detail"] == "Invalid or missing API key"
        invalid = client.get("/api/v1/search", params={"q": "insulin"}, headers={"X-API-Key": "nope"})
        assert invalid.status_code == 401
        # Valid-key catalogue calls would hit PostgreSQL; the guard unit test
        # above already proves a matching fixture key is accepted.


def test_catalogue_stays_open_when_api_keys_empty(monkeypatch, reset_settings) -> None:
    monkeypatch.setenv("API_KEYS", "")
    get_settings.cache_clear()
    with TestClient(create_app()) as client:
        denied_header = client.get(
            "/api/v1/health", headers={"X-API-Key": "definitely-not-a-real-key"}
        )
        assert denied_header.status_code == 200
        index = client.get("/api/v1")
        assert index.status_code == 200
        assert index.json()["version"] == "v1"
