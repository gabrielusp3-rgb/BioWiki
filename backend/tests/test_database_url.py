from app.core.database_url import normalize_database_url


def test_postgres_scheme_becomes_asyncpg() -> None:
    assert (
        normalize_database_url("postgres://u:p@db.example:5432/biowiki")
        == "postgresql+asyncpg://u:p@db.example:5432/biowiki"
    )


def test_postgresql_scheme_gains_asyncpg() -> None:
    assert (
        normalize_database_url("postgresql://u:p@db.example/biowiki")
        == "postgresql+asyncpg://u:p@db.example/biowiki"
    )


def test_sslmode_require_maps_to_asyncpg_ssl() -> None:
    out = normalize_database_url(
        "postgres://u:p@db.example/biowiki?sslmode=require"
    )
    assert out.startswith("postgresql+asyncpg://")
    assert "ssl=require" in out
    assert "sslmode" not in out


def test_empty_stays_empty() -> None:
    assert normalize_database_url("") == ""
    assert normalize_database_url("   ") == ""
