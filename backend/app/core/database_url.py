"""Normalise hosted PostgreSQL URLs for SQLAlchemy + asyncpg."""

from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse


def normalize_database_url(url: str) -> str:
    """Accept postgres:// and postgresql:// strings from managed hosts.

    Cloud providers often issue ``postgres://`` with ``sslmode=require``.
    BioWiki uses asyncpg, which expects ``postgresql+asyncpg://`` and ``ssl=``.
    """
    raw = (url or "").strip()
    if not raw:
        return raw
    if raw.startswith("postgres://"):
        raw = "postgresql://" + raw[len("postgres://") :]
    if raw.startswith("postgresql://") and "+asyncpg" not in raw.split("://", 1)[0]:
        raw = "postgresql+asyncpg://" + raw[len("postgresql://") :]
    parsed = urlparse(raw)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    sslmode = query.pop("sslmode", None)
    if sslmode and "ssl" not in query:
        if sslmode.lower() in {"require", "verify-ca", "verify-full", "true", "1"}:
            query["ssl"] = "require"
        elif sslmode.lower() in {"disable", "allow", "prefer", "false", "0"}:
            query["ssl"] = "false"
    return urlunparse(parsed._replace(query=urlencode(query)))
