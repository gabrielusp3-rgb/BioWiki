"""Opaque offset cursor helpers for list endpoints."""

from __future__ import annotations

import base64


def encode_cursor(offset: int) -> str:
    return base64.urlsafe_b64encode(str(offset).encode()).decode()


_MAX_OFFSET = 1_000_000


def decode_cursor(cursor: str | None) -> int:
    if not cursor:
        return 0
    try:
        offset = int(base64.urlsafe_b64decode(cursor.encode()).decode())
    except (ValueError, TypeError, UnicodeDecodeError):
        return 0
    return max(0, min(offset, _MAX_OFFSET))
