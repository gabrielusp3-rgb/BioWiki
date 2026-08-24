"""ASGI smoke checks that do not need a populated catalogue."""

from __future__ import annotations

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
