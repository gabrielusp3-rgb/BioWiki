"""Rfam connector (RNA family database, EMBL-EBI).

Official REST API (documented):
    https://docs.rfam.org/en/latest/api.html
    JSON: https://rfam.org/family/{acc}?content-type=application/json

When rfam.org is unreachable (timeout) or returns 404, this connector falls
back to the official EMBL-EBI FTP family FASTA:

    https://ftp.ebi.ac.uk/pub/databases/Rfam/CURRENT/fasta_files/{acc}.fa.gz

Those files use INSDC headers (``ACC.v/start-end``), which the BIOWIKI fetcher
already resolves via NCBI. The public MySQL database mentioned in the Rfam
docs is a different protocol and is not used here.
"""

from __future__ import annotations

import zlib
from typing import Any

from app.services.connectors.base import BaseConnector
from app.services.connectors.config import ConnectorSettings, get_connector_settings
from app.services.connectors.errors import (
    ConnectorError,
    ConnectorHTTPError,
    ConnectorNotFound,
    ConnectorParseError,
    ConnectorQueryError,
)
from app.services.connectors.models import RawRecord, SearchHit, SearchPage, SourceQuery

RFAM_API_DOC = "https://docs.rfam.org/en/latest/api.html"
RFAM_FTP_FASTA = (
    "https://ftp.ebi.ac.uk/pub/databases/Rfam/CURRENT/fasta_files/{acc}.fa.gz"
)


class RfamConnector(BaseConnector):
    source = "rfam"

    def __init__(self, settings: ConnectorSettings | None = None, **kwargs: Any) -> None:
        settings = settings or get_connector_settings()
        super().__init__(
            base_url=settings.rfam_base_url,
            rate_per_second=settings.rfam_rate_per_second,
            settings=settings,
            **kwargs,
        )

    async def family(self, rfam_acc: str) -> dict[str, Any]:
        """Family metadata as JSON from the documented REST API."""
        acc = rfam_acc.strip()
        return await self.get_json(
            f"family/{acc}",
            params={"content-type": "application/json"},
        )

    async def alignment_fasta(self, rfam_acc: str, *, use_rest: bool = True) -> RawRecord:
        """Family FASTA: documented REST first, official FTP if REST fails."""
        acc = rfam_acc.strip()
        if use_rest:
            try:
                content = await self.get_text(
                    f"family/{acc}/alignment",
                    params={"format": "fasta", "download": "0"},
                    headers={"Accept": "text/plain"},
                )
                return RawRecord(
                    source=self.source, accession=acc, fmt="fasta", content=content
                )
            except ConnectorError:
                pass
        content = await self._alignment_from_ftp(acc)
        return RawRecord(source=self.source, accession=acc, fmt="fasta", content=content)

    async def _alignment_from_ftp(self, acc: str, *, max_chars: int = 120_000) -> str:
        """Official Rfam FTP FASTA (gzip). Stops after enough header text."""
        url = RFAM_FTP_FASTA.format(acc=acc)
        await self._limiter.acquire()
        decompressor = zlib.decompressobj(16 + zlib.MAX_WBITS)
        parts: list[str] = []
        total = 0
        try:
            async with self._client.stream("GET", url) as response:
                if response.status_code == 404:
                    raise ConnectorNotFound(
                        "Record not found.", status_code=404, source=self.source
                    )
                if response.status_code >= 400:
                    raise ConnectorHTTPError(
                        f"Request failed with {response.status_code}.",
                        status_code=response.status_code,
                        source=self.source,
                    )
                async for raw in response.aiter_bytes():
                    try:
                        text = decompressor.decompress(raw).decode("ascii", "replace")
                    except (OSError, zlib.error, UnicodeError) as exc:
                        raise ConnectorParseError(
                            "Failed to decode Rfam FTP FASTA.", source=self.source
                        ) from exc
                    if not text:
                        continue
                    parts.append(text)
                    total += len(text)
                    if total >= max_chars:
                        break
        except ConnectorError:
            raise
        except Exception as exc:  # network/transport after REST already failed
            raise ConnectorParseError(
                f"Rfam FTP alignment unavailable: {exc}", source=self.source
            ) from exc
        content = "".join(parts)
        if not content.strip():
            raise ConnectorParseError(
                "Rfam FTP alignment was empty.", source=self.source
            )
        return content

    async def find(self, query: SourceQuery) -> SearchPage:
        """Standardised lookup over the Rfam API.

        Rfam's public API is keyed by family accession (RFxxxxx) or family ID
        (e.g. ``tRNA``); it has no organism/gene/PubMed search endpoint, so
        those criteria raise :class:`ConnectorQueryError` instead of returning
        approximated results.
        """
        if query.sequence_type and query.sequence_type.lower() not in {"rna"}:
            raise ConnectorQueryError(
                "Rfam catalogues RNA families only.", source=self.source
            )
        identifier = (query.accession or query.text or "").strip()
        if not identifier:
            raise ConnectorQueryError(
                "Rfam lookup requires a family accession (RFxxxxx) or family ID "
                "(e.g. 'tRNA'); organism/gene/PubMed search is not offered by "
                "the Rfam API.",
                source=self.source,
            )
        try:
            payload = await self.family(identifier)
        except ConnectorNotFound:
            return SearchPage(source=self.source, hits=[], total=0, next_cursor=None)
        except ConnectorError:
            return SearchPage(source=self.source, hits=[], total=0, next_cursor=None)

        entry = payload.get("rfam", payload) if isinstance(payload, dict) else {}
        acc = str(entry.get("acc") or identifier)
        hit = SearchHit(
            source=self.source,
            identifier=acc,
            title=entry.get("id") or entry.get("description"),
            data=entry if isinstance(entry, dict) else None,
        )
        return SearchPage(source=self.source, hits=[hit], total=1, next_cursor=None)
