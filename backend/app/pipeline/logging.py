"""Pipeline logging setup (idempotent, stderr, structured-ish format)."""

from __future__ import annotations

import logging
import sys

from app.core.stdio import configure_utf8_stdio

_CONFIGURED: set[str] = set()
_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"


def get_logger(name: str = "biowiki.pipeline") -> logging.Logger:
    configure_utf8_stdio()
    logger = logging.getLogger(name)
    if name not in _CONFIGURED:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter(_FORMAT))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
        _CONFIGURED.add(name)
    return logger
