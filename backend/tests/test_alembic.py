"""Upgrade an empty PostgreSQL database with Alembic and exercise search_vector.

Uses a dedicated database (never the live catalogue). Inserted rows are
synthetic schema probes, not scientific records.

Prefers CREATE DATABASE on the application cluster when the role has CREATEDB.
Otherwise starts a throwaway PostgreSQL data directory on a free localhost
port so the empty-database checkpoint can still be proven.
"""

from __future__ import annotations

import os
import shutil
import socket
import stat
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.engine.url import make_url
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import get_settings

TEST_DB_NAME = "biowiki_alembic_test"
BACKEND_DIR = Path(__file__).resolve().parents[1]
_PG_BIN_CANDIDATES = (
    Path(r"C:\Program Files\PostgreSQL\17\bin"),
    Path(r"C:\Program Files\PostgreSQL\16\bin"),
    Path("/usr/lib/postgresql/17/bin"),
    Path("/usr/lib/postgresql/16/bin"),
    Path("/usr/pgsql-17/bin"),
    Path("/usr/pgsql-16/bin"),
)


def _with_database(url: str, database: str) -> str:
    return make_url(url).set(database=database).render_as_string(hide_password=False)


def _is_createdb_denied(exc: BaseException) -> bool:
    names = type(exc).__name__.lower()
    orig = getattr(exc, "orig", None)
    if orig is not None:
        names += type(orig).__name__.lower()
    blob = str(exc).lower()
    if "insufficientprivilege" in names:
        return True
    if "permission denied" in blob:
        return True
    # pt-BR: "permissão negada ao criar banco de dados"
    if "permiss" in blob and "banco" in blob:
        return True
    return False


def _find_pg_bin() -> Path | None:
    which = shutil.which("initdb")
    if which:
        return Path(which).resolve().parent
    suffix = "initdb.exe" if os.name == "nt" else "initdb"
    for candidate in _PG_BIN_CANDIDATES:
        if (candidate / suffix).is_file():
            return candidate
    return None


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _rmtree(path: Path) -> None:
    def _onerror(func, name, _exc) -> None:
        os.chmod(name, stat.S_IWRITE)
        func(name)

    shutil.rmtree(path, onerror=_onerror)


@dataclass
class EphemeralPostgres:
    data_dir: Path
    port: int
    bin_dir: Path
    process: subprocess.Popen[bytes] | None = None
    log_handle: object | None = None

    @property
    def url(self) -> str:
        return f"postgresql+asyncpg://postgres:@127.0.0.1:{self.port}/postgres"

    def stop(self) -> None:
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=5)
        handle = self.log_handle
        if handle is not None:
            try:
                handle.close()
            except Exception:
                pass
            self.log_handle = None
        if self.data_dir.exists():
            # Retry rmtree: Windows can hold files briefly after kill.
            last_exc: Exception | None = None
            for _ in range(10):
                try:
                    _rmtree(self.data_dir)
                    last_exc = None
                    break
                except Exception as exc:  # noqa: BLE001
                    last_exc = exc
                    time.sleep(0.2)
            if last_exc is not None:
                raise last_exc


def _wait_for_postgres(port: int) -> None:
    last: OSError | None = None
    for _ in range(80):
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                time.sleep(0.3)
                return
        except OSError as exc:
            last = exc
            time.sleep(0.25)
    raise AssertionError(f"ephemeral PostgreSQL port {port} never opened: {last}")


def _start_ephemeral_postgres() -> EphemeralPostgres:
    bin_dir = _find_pg_bin()
    assert bin_dir is not None, (
        "The API role cannot CREATE DATABASE and initdb was not found. "
        "Grant CREATEDB to the API role or install PostgreSQL server binaries."
    )
    initdb = bin_dir / ("initdb.exe" if os.name == "nt" else "initdb")
    postgres = bin_dir / ("postgres.exe" if os.name == "nt" else "postgres")
    data_dir = Path(tempfile.mkdtemp(prefix="biowiki_alembic_pg_"))
    port = _free_port()
    cluster = EphemeralPostgres(data_dir=data_dir, port=port, bin_dir=bin_dir)
    try:
        init = subprocess.run(
            [
                str(initdb),
                "-D",
                str(data_dir),
                "-U",
                "postgres",
                "-A",
                "trust",
                "-E",
                "UTF8",
                "--no-locale",
                "--no-instructions",
                "-N",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert init.returncode == 0, init.stdout + "\n" + init.stderr
        log_file = data_dir / "postgres.log"
        log_handle = log_file.open("w", encoding="utf-8")
        try:
            proc = subprocess.Popen(
                [
                    str(postgres),
                    "-D",
                    str(data_dir),
                    "-p",
                    str(port),
                    "-h",
                    "127.0.0.1",
                ],
                stdout=log_handle,
                stderr=subprocess.STDOUT,
            )
        except Exception:
            log_handle.close()
            raise
        cluster.process = proc
        cluster.log_handle = log_handle
        if proc.poll() is not None:
            log_handle.close()
            extra = log_file.read_text(encoding="utf-8", errors="replace")
            raise AssertionError(f"postgres.exe exited immediately: {extra}")
        _wait_for_postgres(port)
        return cluster
    except Exception:
        cluster.stop()
        raise


async def _admin_execute(prod_url: str, sql: str) -> None:
    engine = create_async_engine(
        _with_database(prod_url, "postgres"), isolation_level="AUTOCOMMIT"
    )
    try:
        async with engine.connect() as conn:
            await conn.execute(text(sql))
    finally:
        await engine.dispose()


async def _reset_test_database(prod_url: str) -> None:
    terminator = (
        "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
        f"WHERE datname = '{TEST_DB_NAME}' AND pid <> pg_backend_pid()"
    )
    await _admin_execute(prod_url, terminator)
    await _admin_execute(prod_url, f"DROP DATABASE IF EXISTS {TEST_DB_NAME}")
    await _admin_execute(prod_url, f"CREATE DATABASE {TEST_DB_NAME}")


async def _drop_test_database(prod_url: str) -> None:
    terminator = (
        "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
        f"WHERE datname = '{TEST_DB_NAME}' AND pid <> pg_backend_pid()"
    )
    await _admin_execute(prod_url, terminator)
    await _admin_execute(prod_url, f"DROP DATABASE IF EXISTS {TEST_DB_NAME}")


async def _assert_upgraded_schema(test_url: str) -> None:
    engine = create_async_engine(test_url)
    try:
        async with engine.begin() as conn:
            tables = set(
                (
                    await conn.execute(
                        text(
                            "SELECT tablename FROM pg_tables "
                            "WHERE schemaname = 'public'"
                        )
                    )
                ).scalars()
            )
            required = {
                "sequences",
                "organisms",
                "data_sources",
                "publications",
                "genes",
                "genome_records",
                "taxonomy",
                "ingestion_runs",
            }
            assert required <= tables

            gen = (
                await conn.execute(
                    text(
                        """
                        SELECT is_generated, generation_expression
                        FROM information_schema.columns
                        WHERE table_schema = 'public'
                          AND table_name = 'sequences'
                          AND column_name = 'search_vector'
                        """
                    )
                )
            ).one()
            assert gen.is_generated == "ALWAYS"
            assert "to_tsvector" in (gen.generation_expression or "").lower()

            idx = set(
                (
                    await conn.execute(
                        text(
                            "SELECT indexname FROM pg_indexes "
                            "WHERE tablename = 'sequences'"
                        )
                    )
                ).scalars()
            )
            assert "ix_sequences_search_vector" in idx

            await conn.execute(
                text(
                    """
                    INSERT INTO data_sources (key, name)
                    VALUES ('schema_probe', 'Schema probe source')
                    """
                )
            )
            source_id = (
                await conn.execute(
                    text("SELECT id FROM data_sources WHERE key = 'schema_probe'")
                )
            ).scalar_one()
            await conn.execute(
                text(
                    """
                    INSERT INTO organisms (slug, scientific_name, tax_id, "group")
                    VALUES (
                        'schema-probe-organism',
                        'Schema probe organism',
                        2147483646,
                        'bacteria'
                    )
                    """
                )
            )
            organism_id = (
                await conn.execute(
                    text(
                        "SELECT id FROM organisms "
                        "WHERE slug = 'schema-probe-organism'"
                    )
                )
            ).scalar_one()
            await conn.execute(
                text(
                    """
                    INSERT INTO sequences (
                        seq_type, accession, name, description, gene_name,
                        organism_id, source_id, length, residues
                    )
                    VALUES (
                        'dna', 'BW_SCHEMA_PROBE_1', 'schema probe sequence',
                        'alembic search_vector probe phrase', 'PROBE1',
                        :organism_id, :source_id, 4, 'ATGC'
                    )
                    """
                ),
                {"organism_id": organism_id, "source_id": source_id},
            )
            vector = (
                await conn.execute(
                    text(
                        "SELECT search_vector FROM sequences "
                        "WHERE accession = 'BW_SCHEMA_PROBE_1'"
                    )
                )
            ).scalar_one()
            assert vector
            hit = (
                await conn.execute(
                    text(
                        """
                        SELECT accession FROM sequences
                        WHERE search_vector @@ websearch_to_tsquery(
                            'english', 'alembic search_vector probe'
                        )
                        """
                    )
                )
            ).scalar_one()
            assert hit == "BW_SCHEMA_PROBE_1"
            stamped = (
                await conn.execute(text("SELECT version_num FROM alembic_version"))
            ).scalar_one()
            assert stamped == "0004_publication_abstract"
    finally:
        await engine.dispose()


async def test_alembic_upgrade_empty_database_search_vector() -> None:
    prod_url = get_settings().database_url
    parsed = make_url(prod_url)
    assert parsed.database != TEST_DB_NAME

    ephemeral: EphemeralPostgres | None = None
    used_live_cluster = False
    try:
        try:
            await _reset_test_database(prod_url)
            test_url = _with_database(prod_url, TEST_DB_NAME)
            used_live_cluster = True
        except ProgrammingError as exc:
            if not _is_createdb_denied(exc):
                raise
            ephemeral = _start_ephemeral_postgres()
            test_url = ephemeral.url

        env = os.environ.copy()
        env["DATABASE_URL"] = test_url
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "alembic",
                "-x",
                f"url={test_url}",
                "upgrade",
                "head",
            ],
            cwd=BACKEND_DIR,
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stdout + "\n" + result.stderr
        await _assert_upgraded_schema(test_url)
    finally:
        if used_live_cluster:
            await _drop_test_database(prod_url)
        if ephemeral is not None:
            ephemeral.stop()
