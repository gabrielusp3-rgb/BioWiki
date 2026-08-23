"""Async token-bucket rate limiter shared by connectors.

Each connector owns its own limiter instance so per-source limits stay isolated
and independent.
"""

from __future__ import annotations

import asyncio
import time


class AsyncRateLimiter:
    """Token bucket allowing short bursts up to ``capacity`` at ``rate`` tok/s."""

    def __init__(self, rate_per_second: float, capacity: int | None = None) -> None:
        if rate_per_second <= 0:
            raise ValueError("rate_per_second must be positive")
        self._rate = float(rate_per_second)
        self._capacity = float(capacity if capacity is not None else max(1, int(rate_per_second)))
        self._tokens = self._capacity
        self._updated = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            while True:
                now = time.monotonic()
                elapsed = now - self._updated
                self._tokens = min(self._capacity, self._tokens + elapsed * self._rate)
                self._updated = now
                if self._tokens >= 1:
                    self._tokens -= 1
                    return
                deficit = 1 - self._tokens
                await asyncio.sleep(deficit / self._rate)
