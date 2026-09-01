"""Run a command with production DATABASE_URL loaded. Does not print secrets."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.database_url import normalize_database_url


def main() -> int:
    merged: dict[str, str] = {}
    for name in (".env", ".env.production.local"):
        path = ROOT / name
        if not path.exists():
            continue
        for key, value in dotenv_values(path).items():
            if key and value is not None:
                merged[key] = value
    for key, value in merged.items():
        os.environ[key] = value
    url = normalize_database_url(
        merged.get("DATABASE_URL_UNPOOLED") or merged.get("DATABASE_URL") or ""
    )
    if not url or "neon.tech" not in url:
        print("production database url missing or not Neon; aborting", file=sys.stderr)
        return 2
    os.environ["DATABASE_URL"] = url
    os.environ["DATABASE_URL_UNPOOLED"] = url
    os.environ["BIOWIKI_ENV"] = "production"
    os.environ["DATABASE_SSL"] = "true"
    cmd = sys.argv[1:]
    if not cmd:
        print("usage: python scripts/with_production_env.py <command>...", file=sys.stderr)
        return 2
    return subprocess.call(cmd, cwd=str(ROOT))


if __name__ == "__main__":
    raise SystemExit(main())
