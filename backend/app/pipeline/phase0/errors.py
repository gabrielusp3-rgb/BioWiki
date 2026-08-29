"""Map connector / HTTP failures onto audit statuses.

429, timeout, 5xx and transport errors are TEMPORARILY_UNVERIFIED.
They never imply that an accession is scientifically invalid.
"""

from __future__ import annotations

from app.services.connectors.errors import (
    ConnectorError,
    ConnectorHTTPError,
    ConnectorNotFound,
    ConnectorParseError,
    ConnectorRateLimited,
    ConnectorTimeout,
    ConnectorUnavailable,
)

_RETRYABLE_HTTP = {429, 500, 502, 503, 504}


def classify_external_error(exc: BaseException) -> str:
    if isinstance(exc, ConnectorNotFound):
        return "NOT_FOUND"
    if isinstance(exc, ConnectorRateLimited):
        return "TEMPORARILY_UNVERIFIED"
    if isinstance(exc, ConnectorTimeout):
        return "TEMPORARILY_UNVERIFIED"
    if isinstance(exc, ConnectorUnavailable):
        return "TEMPORARILY_UNVERIFIED"
    if isinstance(exc, ConnectorParseError):
        return "TEMPORARILY_UNVERIFIED"
    if isinstance(exc, ConnectorHTTPError):
        if exc.status_code in _RETRYABLE_HTTP:
            return "TEMPORARILY_UNVERIFIED"
        if exc.status_code == 404:
            return "NOT_FOUND"
        if exc.status_code >= 500:
            return "TEMPORARILY_UNVERIFIED"
        return "TEMPORARILY_UNVERIFIED"
    if isinstance(exc, ConnectorError):
        return "TEMPORARILY_UNVERIFIED"
    if isinstance(exc, (TimeoutError, ConnectionError, OSError)):
        return "TEMPORARILY_UNVERIFIED"
    text = str(exc).lower()
    if any(token in text for token in ("timeout", "429", "temporar", "reset", "dns")):
        return "TEMPORARILY_UNVERIFIED"
    return "TEMPORARILY_UNVERIFIED"
