from __future__ import annotations

import logging

from fastapi import APIRouter

from app.api.v1.routers import (
    download,
    genomes,
    meta,
    organisms,
    proteins,
    publications,
    search,
    sequences,
    statistics,
    virus,
)

logger = logging.getLogger("biowiki.api")

api_router = APIRouter()
api_router.include_router(meta.router)
api_router.include_router(sequences.router)
api_router.include_router(proteins.router)
api_router.include_router(virus.router)
api_router.include_router(organisms.router)
try:
    from app.api.v1.routers import paleogenomics

    api_router.include_router(paleogenomics.router)
except Exception:
    logger.exception("Paleogenomics routes failed to load; catalogue routes still served")
api_router.include_router(genomes.router)
api_router.include_router(publications.router)
api_router.include_router(search.router)
api_router.include_router(statistics.router)
api_router.include_router(download.router)
