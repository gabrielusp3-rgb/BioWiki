"""Windows/UTF-8 stdio: integrity reports must encode without cp1252 errors."""

from __future__ import annotations

import json
import sys

from app.core.stdio import configure_utf8_stdio


def test_configure_utf8_stdio_encodes_integrity_symbols() -> None:
    configure_utf8_stdio()
    payload = json.dumps(
        {
            "ok": True,
            "detail": "every sequence↔publication link points to a real sequence",
        },
        ensure_ascii=False,
    )
    encoding = sys.stdout.encoding or "utf-8"
    encoded = payload.encode(encoding, errors="strict")
    assert "sequence↔publication".encode("utf-8") in encoded or encoding.lower().replace("-", "") in {
        "utf8",
        "utf_8",
    }


def test_configure_utf8_stdio_is_idempotent() -> None:
    configure_utf8_stdio()
    configure_utf8_stdio()
    assert sys.stdout.encoding is not None
