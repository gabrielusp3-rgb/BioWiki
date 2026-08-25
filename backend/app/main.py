"""BIOWIKI FastAPI application entrypoint."""

from __future__ import annotations

import os
import subprocess
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.openapi.utils import get_openapi
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.rate_limit import RateLimitMiddleware

BACKEND_ROOT = Path(__file__).resolve().parents[1]


def _migrate_if_hosted() -> None:
    if os.environ.get("PYTEST_CURRENT_TEST") or "pytest" in sys.modules:
        return
    if not os.environ.get("VERCEL"):
        return
    subprocess.check_call(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=str(BACKEND_ROOT),
    )


@asynccontextmanager
async def lifespan(_app: FastAPI):
    _migrate_if_hosted()
    yield


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        return response


def _description(settings) -> str:
    return f"""**BIOWIKI** - Universal Biological Sequence Database API.

Programmatic access to real biological sequences (DNA, RNA, proteins, CRISPR
guides, viruses and genomes) sourced from recognised international databases.

**Base URL (production):** `https://biowiki-api.vercel.app`
**Version prefix:** `/api/v1`
**OpenAPI UI:** `/docs` | **Schema:** `/openapi.json`

**Authentication:** optional for the public read-only API; rate limiting applies.
If `API_KEYS` is unset, catalogue routes are open (the `X-API-Key` header is
ignored). If `API_KEYS` is set, catalogue routes require
`X-API-Key: <YOUR_API_KEY>` and return **401** when the header is missing or
unknown. Never send a real key in examples.

Always public (no key): `/`, `/api/v1`, `/docs`, `/redoc`, `/openapi.json`,
`/api/v1/health`, `/api/v1/ready`.

**Rate limit:** {settings.rate_limit_requests} requests per
{settings.rate_limit_window_seconds} seconds per API process. Exceeding it
returns **429** with `Retry-After`. Exempt: `/`, `/docs`, `/redoc`,
`/openapi.json`, `/api/v1`, `/api/v1/health`.

**Pagination:** list endpoints return `nextCursor`; pass it as `cursor`.

**HTTP:** 200 OK, 401 invalid or missing key (only when `API_KEYS` is set),
404 not found, 422 validation, 429 rate limit.

**Downloads:** `GET /api/v1/download/sequence/{{accession}}?format=fasta|genbank|json`
and bulk `GET /api/v1/download/sequences` (`fasta`, `csv`, `json`).
"""


TAGS_METADATA = [
    {"name": "meta", "description": "Health and readiness probes."},
    {"name": "sequences", "description": "DNA, RNA and CRISPR guide records."},
    {"name": "proteins", "description": "Protein records (UniProt/RefSeq/PDB)."},
    {"name": "virus", "description": "Viral genomes and segments."},
    {"name": "organisms", "description": "Organisms / taxonomy (NCBI tax IDs)."},
    {"name": "genomes", "description": "Whole-genome assembly records (NCBI Assembly)."},
    {"name": "publications", "description": "Scientific literature linked to sequences (PubMed)."},
    {"name": "search", "description": "Global full-text search and autocomplete."},
    {"name": "statistics", "description": "Live database statistics (real aggregates)."},
    {"name": "download", "description": "Exports in FASTA, GenBank, CSV and JSON."},
]


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="BIOWIKI API",
        description=_description(settings),
        version=settings.api_version,
        openapi_tags=TAGS_METADATA,
        lifespan=lifespan,
        servers=[
            {"url": "https://biowiki-api.vercel.app", "description": "Production"},
            {"url": "http://127.0.0.1:8000", "description": "Local development"},
        ],
        contact={"name": "BIOWIKI", "url": "https://github.com/gabrielusp3-rgb/BioWiki"},
        license_info={
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT",
        },
    )

    cors_kwargs: dict = {
        "allow_origins": settings.cors_origins_list,
        "allow_credentials": True,
        "allow_methods": ["GET", "HEAD", "OPTIONS"],
        "allow_headers": ["*"],
    }
    if settings.cors_origin_regex:
        cors_kwargs["allow_origin_regex"] = settings.cors_origin_regex
    elif not settings.is_production:
        # Ngrok preview tunnels are a local-dev convenience, not a production origin.
        cors_kwargs["allow_origin_regex"] = r"https://.*\.ngrok-free\.app"
    app.add_middleware(CORSMiddleware, **cors_kwargs)
    app.add_middleware(GZipMiddleware, minimum_size=500)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(
        RateLimitMiddleware,
        enabled=settings.rate_limit_enabled,
        limit=settings.rate_limit_requests,
        window_seconds=settings.rate_limit_window_seconds,
    )

    app.include_router(api_router, prefix="/api/v1")

    @app.get("/", include_in_schema=False)
    async def root() -> dict:
        return {"name": "BIOWIKI API", "docs": "/docs", "api": "/api/v1"}

    @app.get("/api/v1", tags=["meta"], summary="API v1 index")
    @app.get("/api/v1/", include_in_schema=False)
    async def api_v1_index() -> dict:
        return {
            "name": "BIOWIKI API",
            "version": "v1",
            "docs": "/docs",
            "openapi": "/openapi.json",
            "health": "/api/v1/health",
        }

    def _openapi() -> dict:
        if app.openapi_schema:
            return app.openapi_schema
        schema = get_openapi(
            title=app.title,
            version=app.version,
            openapi_version=app.openapi_version,
            description=app.description,
            routes=app.routes,
            tags=app.openapi_tags,
            servers=app.servers,
            contact=app.contact,
            license_info=app.license_info,
        )
        components = schema.setdefault("components", {})
        components["securitySchemes"] = {
            "ApiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key",
                "description": (
                    "Optional. Required only when the server has API_KEYS set. "
                    "Example: X-API-Key: <YOUR_API_KEY>"
                ),
            }
        }
        schema["security"] = [{}, {"ApiKeyAuth": []}]
        app.openapi_schema = schema
        return schema

    app.openapi = _openapi  # type: ignore[method-assign]
    return app


app = create_app()
