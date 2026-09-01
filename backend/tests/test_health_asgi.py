"""ASGI smoke checks that do not need a populated catalogue."""

from __future__ import annotations

import json

from fastapi.testclient import TestClient

from app.main import app


def test_health_via_asgi() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


def test_root_via_asgi() -> None:
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        body = response.json()
        assert body["docs"] == "/docs"
        assert body["api"] == "/api/v1"


def test_v1_index_via_asgi() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1")
        assert response.status_code == 200
        body = response.json()
        assert body["version"] == "v1"
        assert body["docs"] == "/docs"
        assert body["health"] == "/api/v1/health"


def test_openapi_documents_optional_api_key() -> None:
    with TestClient(app) as client:
        schema = client.get("/openapi.json").json()
    description = schema["info"]["description"]
    assert "YOUR_API_KEY" in description
    assert "nextCursor" in description
    paths = schema.get("paths") or {}
    sequence_list = paths.get("/api/v1/sequences") or paths.get("/sequences")
    assert sequence_list, list(paths)[:8]
    paleo = paths.get("/api/v1/paleogenomics") or paths.get("/paleogenomics")
    assert paleo, list(paths)[:12]
    assert "nextCursor" in json.dumps(sequence_list)
    assert "`nextCursor`" not in description
    assert "`cursor`" not in description
    assert "401" in description
    # Exact server URL advertised by this application's OpenAPI document.
    # This is not sanitization of a user-supplied URL (CodeQL py/incomplete-url-substring-sanitization).
    servers = [item.get("url") for item in schema.get("servers") or []]
    assert any(server == "https://biowiki-api.vercel.app" for server in servers)
    scheme = schema["components"]["securitySchemes"]["ApiKeyAuth"]
    assert scheme["name"] == "X-API-Key"
    assert "YOUR_API_KEY" in scheme["description"]
    assert {} in schema["security"]
    assert {"ApiKeyAuth": []} in schema["security"]
