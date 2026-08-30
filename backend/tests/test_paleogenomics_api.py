"""Paleogenomics HTTP tests against the running API."""

from __future__ import annotations

import httpx
import pytest

pytestmark = pytest.mark.live


def test_paleogenomics_landing(api: httpx.Client) -> None:
    response = api.get("/paleogenomics")
    assert response.status_code == 200
    body = response.json()
    overview = body["overview"]
    assert overview["speciesCount"] >= 0
    assert overview["sequenceCount"] >= 0
    assert "notes" in body
    assert "species" in body
    assert "featured" in body


def test_paleogenomics_statistics_are_live(api: httpx.Client) -> None:
    landing = api.get("/paleogenomics").json()["overview"]
    stats = api.get("/paleogenomics/statistics")
    assert stats.status_code == 200
    body = stats.json()
    assert body["speciesCount"] == landing["speciesCount"]
    assert body["sequenceCount"] == landing["sequenceCount"]


def test_paleogenomics_unknown_slug(api: httpx.Client) -> None:
    response = api.get("/paleogenomics/species/definitely-not-a-paleogenomic-taxon")
    assert response.status_code == 404


def test_paleogenomics_invalid_filter(api: httpx.Client) -> None:
    response = api.get("/paleogenomics/species", params={"subsection": "not-a-subsection"})
    assert response.status_code == 422


def test_paleogenomics_rejects_unbounded_page(api: httpx.Client) -> None:
    response = api.get("/paleogenomics/species", params={"limit": 500})
    assert response.status_code == 422


def test_paleogenomics_introgression_is_not_ancient_dna(api: httpx.Client) -> None:
    response = api.get("/paleogenomics/introgression", params={"limit": 20})
    assert response.status_code == 200
    body = response.json()
    assert "note" in body
    assert "nextCursor" in body
    for row in body.get("results") or []:
        assert "sapiens" in (row.get("modernScientificName") or "").lower()
        assert row.get("archaicSource") in {"neanderthal", "denisovan", "unknown_archaic"}


def test_paleogenomics_species_when_seeded(api: httpx.Client) -> None:
    listing = api.get("/paleogenomics/species", params={"limit": 20})
    assert listing.status_code == 200
    payload = listing.json()
    assert "nextCursor" in payload
    results = payload.get("results") or []
    if payload["total"] == 0:
        pytest.skip("Paleogenomics catalogue is not seeded")
    slugs = {item["slug"] for item in results}
    assert "raphus-cucullatus" in slugs
    dodo = api.get("/paleogenomics/species/raphus-cucullatus")
    assert dodo.status_code == 200
    body = dodo.json()
    assert body["taxId"] == 187135
    assert body["scientificName"] == "Raphus cucullatus"
    nested = api.get(
        "/paleogenomics/species/raphus-cucullatus/sequences", params={"limit": 5}
    )
    assert nested.status_code == 200
    seq_body = nested.json()
    assert "nextCursor" in seq_body
    for row in seq_body.get("results") or []:
        assert row["seqType"] != "genome"
        assert row["seqType"] in {"dna", "rna", "protein"}


def test_search_surfaces_paleogenomics_profiles(api: httpx.Client) -> None:
    response = api.get("/search", params={"q": "dodo", "limit": 5})
    assert response.status_code == 200
    body = response.json()
    profiles = body.get("paleogenomicsProfiles") or []
    if not profiles:
        landing = api.get("/paleogenomics").json()
        if landing["overview"]["speciesCount"] == 0:
            pytest.skip("Paleogenomics catalogue is not seeded")
        pytest.fail("seeded Paleogenomics collection did not surface on search for dodo")
    assert any(
        item.get("slug") == "raphus-cucullatus"
        or "cucullatus" in (item.get("scientificName") or "").lower()
        for item in profiles
    )
