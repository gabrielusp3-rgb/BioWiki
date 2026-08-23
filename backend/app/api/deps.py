"""Shared API dependencies."""

from __future__ import annotations

from typing import Annotated

from fastapi import Header, HTTPException, Path, status

from app.core.config import get_settings
from app.database.session import get_session  # re-exported for routers

# Path identifiers are looked up in PostgreSQL, never used as filesystem paths.
# Length caps block oversized-URL DoS without rejecting real NCBI/UniProt IDs.
AccessionPath = Annotated[str, Path(min_length=1, max_length=64)]
OrganismIdPath = Annotated[str, Path(min_length=1, max_length=128)]

__all__ = ["get_session", "api_key_guard", "AccessionPath", "OrganismIdPath"]


async def api_key_guard(x_api_key: str | None = Header(default=None)) -> None:
    """Optional API-key check.

    If ``API_KEYS`` is empty (local development) the API is open. When keys are
    configured, requests must present a valid one via ``X-API-Key``.
    """
    keys = get_settings().api_keys_list
    if keys and (x_api_key not in keys):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API key"
        )
