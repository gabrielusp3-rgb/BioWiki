"""Security unit tests. No production rows are written."""

from __future__ import annotations

import base64

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.testclient import TestClient

from app.core.rate_limit import RateLimitMiddleware
from app.schemas.common import ListResponse
from app.services.export_service import safe_download_filename
from app.services.pagination import decode_cursor


async def _ok(_request: Request) -> PlainTextResponse:
    return PlainTextResponse("ok")


def test_safe_download_filename_strips_crlf_and_quotes() -> None:
    name = safe_download_filename('NM_000207";\r\nLocation: x', ".fasta")
    assert "\r" not in name
    assert "\n" not in name
    assert '"' not in name
    assert "/" not in name
    assert "\\" not in name
    assert name.endswith(".fasta")


def test_safe_download_filename_keeps_real_accessions() -> None:
    assert safe_download_filename("NG_074726", ".fasta") == "NG_074726.fasta"
    assert safe_download_filename("NM_000207.3", ".gb") == "NM_000207.3.gb"


def test_list_response_serializes_next_cursor_as_camel_case() -> None:
    payload = ListResponse[dict](results=[{"accession": "NM_000207"}], total=21, next_cursor="Mg")
    dumped = payload.model_dump(by_alias=True)
    assert dumped["nextCursor"] == "Mg"
    assert dumped["total"] == 21
    assert "next_cursor" not in dumped


def test_decode_cursor_caps_huge_offsets() -> None:
    huge = base64.urlsafe_b64encode(b"999999999999").decode()
    assert decode_cursor(huge) == 1_000_000
    assert decode_cursor("not-a-cursor") == 0
    assert decode_cursor(None) == 0
    invalid_utf8 = base64.urlsafe_b64encode(bytes([0xFF, 0xFE, 0xFD])).decode()
    assert decode_cursor(invalid_utf8) == 0


def test_rate_limit_middleware_blocks_after_limit() -> None:
    app = Starlette(routes=[])
    app.add_route("/api/v1/search", _ok)
    app.add_route("/api/v1/health", _ok)
    app.add_middleware(RateLimitMiddleware, enabled=True, limit=3, window_seconds=60)
    client = TestClient(app)
    assert client.get("/api/v1/search").status_code == 200
    assert client.get("/api/v1/search").status_code == 200
    assert client.get("/api/v1/search").status_code == 200
    blocked = client.get("/api/v1/search")
    assert blocked.status_code == 429
    assert blocked.json()["detail"] == "Rate limit exceeded"
    assert blocked.headers.get("retry-after") == "60"
    assert client.get("/api/v1/health").status_code == 200


def test_ready_probe_is_rate_limited() -> None:
    app = Starlette(routes=[])
    app.add_route("/api/v1/ready", _ok)
    app.add_middleware(RateLimitMiddleware, enabled=True, limit=2, window_seconds=60)
    client = TestClient(app)
    assert client.get("/api/v1/ready").status_code == 200
    assert client.get("/api/v1/ready").status_code == 200
    assert client.get("/api/v1/ready").status_code == 429
