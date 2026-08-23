"""BIOWIKI FastAPI application entrypoint."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.rate_limit import RateLimitMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        return response

DESCRIPTION = """**BIOWIKI** — Universal Biological Sequence Database API.

Programmatic access to real biological sequences (DNA, RNA, proteins, CRISPR
guides, viruses and genomes) sourced from recognised international databases.

- Versioned under `/api/v1`
- Cursor-based pagination on list endpoints (`nextCursor`)
- PostgreSQL full-text search on `/search`
- Rate limited; optional API-key authentication via the `X-API-Key` header"""

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
        description=DESCRIPTION,
        version=settings.api_version,
        openapi_tags=TAGS_METADATA,
        contact={"name": "BIOWIKI", "url": "https://biowiki.org/"},
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
    # Ngrok preview tunnels are a local-dev convenience, not a production origin.
    if settings.environment.lower() in {"development", "dev", "local"}:
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

    return app


app = create_app()
