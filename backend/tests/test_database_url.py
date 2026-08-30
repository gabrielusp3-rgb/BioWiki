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


def test_channel_binding_is_stripped_for_asyncpg() -> None:
    out = normalize_database_url(
        "postgres://u:p@db.example/biowiki?sslmode=require&channel_binding=require"
    )
    assert "channel_binding" not in out
    assert "ssl=require" in out


def test_empty_stays_empty() -> None:
    assert normalize_database_url("") == ""
    assert normalize_database_url("   ") == ""


def test_unpooled_url_is_preferred(monkeypatch) -> None:
    from app.core.config import Settings

    monkeypatch.setenv(
        "DATABASE_URL",
        "postgres://u:p@ep-pooler.example/db?sslmode=require",
    )
    monkeypatch.setenv(
        "DATABASE_URL_UNPOOLED",
        "postgres://u:p@ep-direct.example/db?sslmode=require",
    )
    settings = Settings()
    assert "ep-direct.example" in settings.database_url
    assert "ep-pooler.example" not in settings.database_url
    assert settings.database_url.startswith("postgresql+asyncpg://")
