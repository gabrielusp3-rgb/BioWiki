"""Base async connector: shared HTTP client with timeout, retry and rate limit.

Design goals:
- **Decoupled**: connectors depend only on this base + their own config; nothing
  in the app imports a connector unless it explicitly needs one.
- **Resilient**: bounded timeouts, exponential backoff with jitter on transient
  failures (network errors, 429, 5xx), and typed errors otherwise.
- **Polite**: per-source token-bucket rate limiting and a descriptive UA.
"""

from __future__ import annotations

import asyncio
import random
from typing import Any

import httpx

from app.services.connectors.config import ConnectorSettings, get_connector_settings
from app.services.connectors.errors import (
    ConnectorHTTPError,
    ConnectorNotFound,
    ConnectorParseError,
    ConnectorRateLimited,
    ConnectorTimeout,
    ConnectorUnavailable,
)
from app.services.connectors.rate_limiter import AsyncRateLimiter

_RETRYABLE_STATUS = {429, 500, 502, 503, 504}


class BaseConnector:
    """Reusable async HTTP client for a single external data source."""

    #: Human-readable source name; overridden by subclasses.
    source: str = "base"

    def __init__(
        self,
        *,
        base_url: str,
        rate_per_second: float,
        settings: ConnectorSettings | None = None,
        default_headers: dict[str, str] | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.settings = settings or get_connector_settings()
        self.base_url = base_url.rstrip("/")
        self._limiter = AsyncRateLimiter(rate_per_second)
        self._owns_client = client is None
        headers = {"User-Agent": self.settings.user_agent, "Accept": "application/json"}
        if default_headers:
            headers.update(default_headers)
        self._client = client or httpx.AsyncClient(
            timeout=httpx.Timeout(self.settings.timeout_seconds),
            headers=headers,
            follow_redirects=True,
        )

    # -- lifecycle ----------------------------------------------------------
    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def __aenter__(self) -> "BaseConnector":
        return self

    async def __aexit__(self, *_exc: object) -> None:
        await self.aclose()

    # -- helpers ------------------------------------------------------------
    def _backoff(self, attempt: int, retry_after: float | None = None) -> float:
        if retry_after is not None:
            return min(retry_after, self.settings.backoff_max_seconds)
        base = self.settings.backoff_base_seconds * (2 ** attempt)
        jitter = random.uniform(0, self.settings.backoff_base_seconds)
        return min(base + jitter, self.settings.backoff_max_seconds)

    @staticmethod
    def _parse_retry_after(response: httpx.Response) -> float | None:
        value = response.headers.get("Retry-After")
        if not value:
            return None
        try:
            return float(value)
        except ValueError:
            return None

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        json_body: Any | None = None,
        content: Any | None = None,
    ) -> httpx.Response:
        """Perform an HTTP request with rate limiting, retries and typed errors."""
        url = path if path.startswith("http") else f"{self.base_url}/{path.lstrip('/')}"
        clean_params = {k: v for k, v in (params or {}).items() if v is not None}
        last_exc: Exception | None = None

        for attempt in range(self.settings.max_retries + 1):
            await self._limiter.acquire()
            try:
                response = await self._client.request(
                    method, url,
                    params=clean_params or None,
                    headers=headers,
                    json=json_body,
                    content=content,
                )
            except httpx.TimeoutException as exc:
                last_exc = exc
                if attempt >= self.settings.max_retries:
                    raise ConnectorTimeout(str(exc), source=self.source) from exc
                await asyncio.sleep(self._backoff(attempt))
                continue
            except httpx.TransportError as exc:
                last_exc = exc
                if attempt >= self.settings.max_retries:
                    raise ConnectorUnavailable(str(exc), source=self.source) from exc
                await asyncio.sleep(self._backoff(attempt))
                continue

            if response.status_code in _RETRYABLE_STATUS:
                retry_after = self._parse_retry_after(response)
                if attempt < self.settings.max_retries:
                    await asyncio.sleep(self._backoff(attempt, retry_after))
                    continue
                if response.status_code == 429:
                    raise ConnectorRateLimited(
                        "Upstream rate limit exceeded.",
                        retry_after=retry_after,
                        source=self.source,
                    )
                raise ConnectorHTTPError(
                    f"Upstream error {response.status_code}.",
                    status_code=response.status_code,
                    source=self.source,
                )

            if response.status_code == 404:
                raise ConnectorNotFound(
                    "Record not found.", status_code=404, source=self.source
                )
            if response.status_code >= 400:
                raise ConnectorHTTPError(
                    f"Request failed with {response.status_code}.",
                    status_code=response.status_code,
                    source=self.source,
                )
            return response

        # Should be unreachable, but keep the type-checker and runtime safe.
        raise ConnectorUnavailable(
            f"Request failed after retries: {last_exc}", source=self.source
        )

    async def get_json(self, path: str, **kwargs: Any) -> Any:
        response = await self.request("GET", path, **kwargs)
        try:
            return response.json()
        except ValueError as exc:
            raise ConnectorParseError(
                "Failed to decode JSON response.", source=self.source
            ) from exc

    async def get_text(self, path: str, **kwargs: Any) -> str:
        response = await self.request("GET", path, **kwargs)
        return response.text

    async def post_json(self, path: str, *, json_body: Any, **kwargs: Any) -> Any:
        response = await self.request("POST", path, json_body=json_body, **kwargs)
        try:
            return response.json()
        except ValueError as exc:
            raise ConnectorParseError(
                "Failed to decode JSON response.", source=self.source
            ) from exc
