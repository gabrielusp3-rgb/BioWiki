"""Rfam source failures must not invent records or abort the pipeline."""

from __future__ import annotations

from app.pipeline.fetchers import rfam as rfam_fetcher
from app.pipeline.fetchers.rfam import _MEMBER_RE
from app.services.connectors.errors import ConnectorNotFound, ConnectorTimeout


class _UnavailableRfam:
    def __init__(self, exc: Exception) -> None:
        self._exc = exc

    async def __aenter__(self) -> "_UnavailableRfam":
        return self

    async def __aexit__(self, *_exc: object) -> None:
        return None

    async def family(self, _acc: str) -> dict:
        raise self._exc

    async def alignment_fasta(self, _acc: str, **_kwargs):
        raise self._exc


async def test_rfam_404_returns_failed_report_without_records(monkeypatch) -> None:
    monkeypatch.setattr(
        rfam_fetcher,
        "RfamConnector",
        lambda: _UnavailableRfam(
            ConnectorNotFound("Record not found.", status_code=404, source="rfam")
        ),
    )
    report = await rfam_fetcher.ingest_family("RF00001")
    assert report.created == 0
    assert report.updated == 0
    assert report.failed == 1
    assert "unavailable" in report.errors[0].lower()
    assert "No records invented" in report.errors[0]


async def test_rfam_timeout_does_not_raise(monkeypatch) -> None:
    monkeypatch.setattr(
        rfam_fetcher,
        "RfamConnector",
        lambda: _UnavailableRfam(ConnectorTimeout("timed out", source="rfam")),
    )
    report = await rfam_fetcher.ingest_family("RF00005")
    assert report.failed == 1
    assert report.created == 0


def test_member_regex_matches_official_ftp_headers() -> None:
    text = (
        ">X01556.1/3-118\nCUUGACGAU\n"
        ">M16174.1/3-119\nUACGGCGGC\n"
        ">AF001265.1/6033-6149\nUACGGCGGU\n"
    )
    accessions = [match.group(1) for match in _MEMBER_RE.finditer(text)]
    assert accessions == ["X01556.1", "M16174.1", "AF001265.1"]
