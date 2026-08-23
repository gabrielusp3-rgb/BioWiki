"""In-process sliding-window rate limiter for the public HTTP API.

Honours RATE_LIMIT_* settings that were already defined but unused. Per-IP
only; health probes are exempt so load balancers are not blocked.
"""

from __future__ import annotations

from collections import defaultdict, deque
from time import monotonic

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

# Liveness only. /ready hits PostgreSQL, so it stays rate-limited.
_EXEMPT_SUFFIXES = ("/health",)
_EXEMPT_PATHS = {"/", "/docs", "/redoc", "/openapi.json"}


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        *,
        enabled: bool = True,
        limit: int = 120,
        window_seconds: int = 60,
    ) -> None:
        super().__init__(app)
        self.enabled = enabled
        self.limit = max(1, int(limit))
        self.window_seconds = max(1, int(window_seconds))
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def _client_key(self, request: Request) -> str:
        if request.client and request.client.host:
            return request.client.host
        return "unknown"

    def _is_exempt(self, path: str) -> bool:
        if path in _EXEMPT_PATHS:
            return True
        return any(path.endswith(suffix) for suffix in _EXEMPT_SUFFIXES)

    def allow(self, key: str) -> bool:
        """Record one hit. Returns False when the window is exhausted."""
        now = monotonic()
        bucket = self._hits[key]
        cutoff = now - self.window_seconds
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        if len(bucket) >= self.limit:
            return False
        bucket.append(now)
        return True

    async def dispatch(self, request: Request, call_next) -> Response:
        if not self.enabled or self._is_exempt(request.url.path):
            return await call_next(request)
        if not self.allow(self._client_key(request)):
            return JSONResponse(
                {"detail": "Rate limit exceeded"},
                status_code=429,
                headers={
                    "Retry-After": str(self.window_seconds),
                    "X-Content-Type-Options": "nosniff",
                    "X-Frame-Options": "DENY",
                    "Referrer-Policy": "no-referrer",
                },
            )
        return await call_next(request)
