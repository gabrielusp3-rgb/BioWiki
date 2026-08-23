"""Connector error hierarchy.

All connectors raise these typed errors so callers can handle failures uniformly
without depending on the underlying HTTP library.
"""

from __future__ import annotations


class ConnectorError(Exception):
    """Base class for all connector failures."""

    def __init__(self, message: str, *, source: str | None = None) -> None:
        super().__init__(message)
        self.source = source


class ConnectorTimeout(ConnectorError):
    """The upstream service did not respond within the timeout budget."""


class ConnectorUnavailable(ConnectorError):
    """Network/transport failure while reaching the upstream service."""


class ConnectorHTTPError(ConnectorError):
    """Upstream returned a non-successful HTTP status."""

    def __init__(self, message: str, *, status_code: int, source: str | None = None) -> None:
        super().__init__(message, source=source)
        self.status_code = status_code


class ConnectorNotFound(ConnectorHTTPError):
    """The requested record does not exist (HTTP 404)."""


class ConnectorRateLimited(ConnectorHTTPError):
    """Upstream rejected the request due to rate limiting (HTTP 429)."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int = 429,
        retry_after: float | None = None,
        source: str | None = None,
    ) -> None:
        super().__init__(message, status_code=status_code, source=source)
        self.retry_after = retry_after


class ConnectorParseError(ConnectorError):
    """The response body could not be parsed into the expected format."""


class ConnectorQueryError(ConnectorError):
    """The requested query is empty or not supported by this source.

    Raised instead of silently returning fabricated or approximate results —
    each source only answers queries its official API actually supports.
    """
