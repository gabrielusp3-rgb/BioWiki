"""Apply Alembic migrations, optionally seed curated records, then start the API.

Used as the process entrypoint in Docker and on hosted PaaS (Render, Railway).
Honours PORT / HOST from the platform. Localhost bind is not used here.
"""

from __future__ import annotations

import asyncio
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


async def _catalogue_is_empty() -> bool:
    from sqlalchemy import func, select

    from app.database.session import get_sessionmaker
    from app.models.sequence import Sequence

    async with get_sessionmaker()() as session:
        count = await session.scalar(select(func.count()).select_from(Sequence))
    return int(count or 0) == 0


def _maybe_seed() -> None:
    flag = os.environ.get("BOOTSTRAP_SEED", "").strip().lower()
    if flag in {"", "0", "false", "no", "off"}:
        return
    force = flag in {"1", "true", "yes", "on", "always"}
    if not force:
        try:
            empty = asyncio.run(_catalogue_is_empty())
        except Exception as exc:  # noqa: BLE001
            print(f"bootstrap: could not count sequences ({exc}); skipping seed")
            return
        if not empty:
            return
    print("bootstrap: empty catalogue — importing curated real accessions")
    subprocess.check_call(
        [sys.executable, "-m", "scripts.seed_initial", "--no-search"]
    )


def main() -> None:
    _upgrade()
    _maybe_seed()
    host = os.environ.get("HOST", "0.0.0.0")
    port = os.environ.get("PORT", "8000")
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        host,
        "--port",
        port,
        "--proxy-headers",
        "--forwarded-allow-ips",
        "*",
    ]
    os.execvp(sys.executable, cmd)


if __name__ == "__main__":
    main()
