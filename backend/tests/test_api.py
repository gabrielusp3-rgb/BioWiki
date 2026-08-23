"""Read-only HTTP tests against the running BIOWIKI API and live records."""

from __future__ import annotations

import httpx


def test_health(api: httpx.Client) -> None:
    response = api.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options") == "DENY"


def test_ready_does_not_expose_internal_errors(api: httpx.Client) -> None:
    response = api.get("/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"ready", "degraded"}
    assert "detail" not in body
    dumped = response.text.lower()
    assert "traceback" not in dumped
    assert "postgresql" not in dumped
    assert "asyncpg" not in dumped


def test_swagger_docs(api_root: httpx.Client) -> None:
    response = api_root.get("/docs")
    assert response.status_code == 200
    assert "swagger" in response.text.lower() or "openapi" in response.text.lower()


def test_statistics_matches_live_dataset(api: httpx.Client) -> None:
    response = api.get("/statistics")
    assert response.status_code == 200
    body = response.json()
    assert body["totalSequences"] == 1542
    assert body["publications"] == 5838
    assert body["organisms"] == 454
    assert body["genomes"] == 32
    keys = {item["key"]: item["count"] for item in body["categories"]}
    assert keys["genome"] == 32


def test_list_sequences_dna(api: httpx.Client) -> None:
    response = api.get("/sequences", params={"type": "dna", "limit": 5})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 5
    assert body["results"]
    assert all(item.get("accession") for item in body["results"])


def test_sequence_detail_nm_000207(api: httpx.Client) -> None:
    response = api.get("/sequences/NM_000207")
    assert response.status_code == 200
    body = response.json()
    assert body["accession"] == "NM_000207"
    assert body.get("sequence")
    assert len(body["sequence"]) > 10


def test_protein_p01308(api: httpx.Client) -> None:
    response = api.get("/proteins/P01308")
    assert response.status_code == 200
    body = response.json()
    assert body["accession"] == "P01308"
    assert body.get("sequence")


def test_search_ins(api: httpx.Client) -> None:
    response = api.get("/search", params={"q": "INS", "limit": 10})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 1
    assert body["results"]


def test_organisms_list_and_detail(api: httpx.Client) -> None:
    listing = api.get("/organisms", params={"limit": 5})
    assert listing.status_code == 200
    payload = listing.json()
    results = payload["organisms"]
    assert results
    identifier = results[0]["slug"]
    detail = api.get(f"/organisms/{identifier}")
    assert detail.status_code == 200
    assert detail.json()["scientificName"]
    assert detail.json()["taxId"]


def test_publications_list_and_pmid(api: httpx.Client) -> None:
    listing = api.get("/publications", params={"limit": 5})
    assert listing.status_code == 200
    results = listing.json().get("results") or []
    assert results
    pmid = results[0]["pubmedId"]
    assert isinstance(pmid, int) and pmid > 0
    detail = api.get(f"/publications/{pmid}")
    assert detail.status_code == 200
    assert detail.json()["pubmedId"] == pmid


def test_crispr_record(api: httpx.Client) -> None:
    response = api.get("/crispr", params={"limit": 1})
    assert response.status_code == 200
    results = response.json()["results"]
    assert results
    accession = results[0]["accession"]
    detail = api.get(f"/sequences/{accession}")
    assert detail.status_code == 200
    assert detail.json()["accession"] == accession


def test_genomes_are_assemblies(api: httpx.Client) -> None:
    response = api.get("/genomes", params={"limit": 100})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 32
    assert len(body["results"]) == 32
    sample = body["results"][0]
    assert sample["accession"]
    assert sample.get("assemblyLevel")
    detail = api.get(f"/genomes/{sample['accession']}")
    assert detail.status_code == 200
    assert detail.json()["accession"] == sample["accession"]


def test_fasta_download_nm_000207(api: httpx.Client) -> None:
    response = api.get("/download/sequence/NM_000207", params={"format": "fasta"})
    assert response.status_code == 200
    text = response.text
    assert text.startswith(">")
    assert "NM_000207" in text.splitlines()[0]
    body = "".join(line.strip() for line in text.splitlines()[1:])
    assert len(body) > 10
    assert set(body.upper()) <= set("ACGTUNRYSWKMBDHV-")


def test_download_index(api: httpx.Client) -> None:
    response = api.get("/download")
    assert response.status_code == 200
    body = response.json()
    assert "fasta" in body["formats"]
    assert body["totalRecords"] == 1542


def test_search_rejects_sql_injection_payloads(api: httpx.Client) -> None:
    payloads = [
        "' OR 1=1 --",
        "1; DROP TABLE sequences;",
        "insulin') OR ('1'='1",
    ]
    for payload in payloads:
        response = api.get("/search", params={"q": payload, "limit": 5})
        assert response.status_code == 200, payload
        body = response.json()
        assert "results" in body
        dumped = response.text.lower()
        assert "syntax error" not in dumped
        assert "pg_" not in dumped


def test_search_rejects_oversized_query(api: httpx.Client) -> None:
    response = api.get("/search", params={"q": "A" * 300})
    assert response.status_code == 422


def test_list_rejects_oversized_organism_filter(api: httpx.Client) -> None:
    response = api.get("/sequences", params={"type": "dna", "organism": "A" * 300})
    assert response.status_code == 422


def test_oversized_accession_path_is_rejected(api: httpx.Client) -> None:
    response = api.get("/sequences/" + ("A" * 65))
    assert response.status_code == 422


def test_path_traversal_accession_is_not_found(api: httpx.Client) -> None:
    response = api.get("/sequences/..%2F..%2Fetc%2Fpasswd")
    assert response.status_code in {404, 422}


def test_download_filename_header_is_safe(api: httpx.Client) -> None:
    response = api.get("/download/sequence/NM_000207", params={"format": "fasta"})
    assert response.status_code == 200
    disposition = response.headers.get("content-disposition", "")
    assert "\r" not in disposition
    assert "\n" not in disposition
    assert "NM_000207.fasta" in disposition


def test_ng_representative_sequence_is_present(api: httpx.Client) -> None:
    response = api.get("/sequences/NG_074726")
    assert response.status_code == 200
    body = response.json()
    assert body["accession"] == "NG_074726"
    assert body.get("sequence")
    assert len(body["sequence"]) == body["length"] == 1013
