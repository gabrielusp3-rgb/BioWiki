"""DDBJ must not be presented as an operational BioWiki connector."""

from __future__ import annotations

from pathlib import Path

from app.services.connectors import __all__ as connector_exports


REPO = Path(__file__).resolve().parents[2]


def test_no_ddbj_connector_export() -> None:
    lowered = {name.lower() for name in connector_exports}
    assert "ddbjconnector" not in lowered
    assert not any("ddbj" in name.lower() for name in connector_exports)


def test_no_ddbj_connector_package() -> None:
    connectors = REPO / "backend" / "app" / "services" / "connectors"
    names = {path.name.lower() for path in connectors.iterdir()}
    assert "ddbj" not in names
    assert not any(path.name.lower().startswith("ddbj") for path in connectors.rglob("*"))


def test_frontend_filters_do_not_offer_ddbj_as_source() -> None:
    dna = (REPO / "frontend" / "src" / "lib" / "dna.ts").read_text(encoding="utf-8")
    virus = (REPO / "frontend" / "src" / "lib" / "virus.ts").read_text(encoding="utf-8")
    assert 'value: "ddbj"' not in dna
    assert 'value: "ddbj"' not in virus


def test_footer_does_not_list_ddbj_as_operational_source() -> None:
    footer = (REPO / "frontend" / "src" / "components" / "layout" / "SiteFooter.tsx").read_text(
        encoding="utf-8"
    )
    assert "DDBJ" not in footer
