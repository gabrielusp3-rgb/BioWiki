"""Apply Alembic migrations, then start the API. Used only inside Docker."""

from __future__ import annotations

import os
import subprocess
import sys
import time


def _upgrade() -> None:
    last_error: Exception | None = None
    for _ in range(30):
        try:
            subprocess.check_call([sys.executable, "-m", "alembic", "upgrade", "head"])
            return
        except subprocess.CalledProcessError as exc:
            last_error = exc
            time.sleep(1)
    raise SystemExit(f"alembic upgrade head failed: {last_error}")


def main() -> None:
    _upgrade()
    os.execvp(
        sys.executable,
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "0.0.0.0",
            "--port",
            "8000",
        ],
    )


if __name__ == "__main__":
    main()
