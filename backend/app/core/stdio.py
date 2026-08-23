"""UTF-8 standard streams for CLI tools on Windows consoles.

Windows often defaults to cp1252. BIOWIKI reports include Unicode (for example
the integrity check text "sequence↔publication"). Encoding those characters as
cp1252 raises UnicodeEncodeError. Reconfiguring stdout/stderr to UTF-8 fixes
the origin of the failure without stripping or replacing scientific text.
Hosts that already use UTF-8 are left unchanged.
"""

from __future__ import annotations

import io
import sys

_CONFIGURED = False


def configure_utf8_stdio() -> None:
    """Ensure stdout and stderr encode Unicode as UTF-8.

    Safe to call more than once. Never substitutes characters with ``?`` or
    ASCII lookalikes; UTF-8 can represent the full report text.
    """
    global _CONFIGURED

    if sys.platform == "win32":
        try:
            import ctypes

            # Console code page 65001 is UTF-8. Failure is non-fatal: the
            # Python stream reconfiguration below still prevents EncodeError.
            ctypes.windll.kernel32.SetConsoleOutputCP(65001)
            ctypes.windll.kernel32.SetConsoleCP(65001)
        except Exception:
            pass

    for name in ("stdout", "stderr"):
        stream = getattr(sys, name, None)
        if stream is None:
            continue
        encoding = (getattr(stream, "encoding", None) or "").lower().replace("-", "")
        if encoding in {"utf8", "utf_8"}:
            continue
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="strict")
                continue
            except (OSError, ValueError, AttributeError):
                pass
        buffer = getattr(stream, "buffer", None)
        if buffer is None:
            continue
        try:
            wrapped = io.TextIOWrapper(
                buffer,
                encoding="utf-8",
                errors="strict",
                line_buffering=bool(getattr(stream, "line_buffering", True)),
            )
            setattr(sys, name, wrapped)
        except (OSError, ValueError, AttributeError):
            continue

    _CONFIGURED = True
