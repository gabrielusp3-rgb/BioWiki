"""RefSeq connector.

RefSeq is NCBI's curated subset. This connector reuses the E-utilities client but
constrains searches to the RefSeq set and validates canonical RefSeq accession
prefixes (NM_, NR_, XM_, XR_, NP_, XP_, NC_, NG_, NW_, NT_, WP_, …).
"""

from __future__ import annotations

import re

from app.services.connectors.config import ConnectorSettings, get_connector_settings
from app.services.connectors.models import RawRecord, SearchPage, SourceQuery, retag_page
from app.services.connectors.ncbi.client import NCBIConnector

# Canonical RefSeq accession prefixes → underscore then digits.
_REFSEQ_RE = re.compile(
    r"^(AC|NC|NG|NT|NW|NZ|NM|NR|XM|XR|NP|AP|XP|YP|WP|ZP)_[0-9]+(\.\d+)?$",
    re.IGNORECASE,
)


def is_refseq_accession(accession: str) -> bool:
    return bool(_REFSEQ_RE.match(accession.strip()))


class RefSeqConnector:
    source = "refseq"

    def __init__(
        self,
        *,
        ncbi: NCBIConnector | None = None,
        settings: ConnectorSettings | None = None,
    ) -> None:
        self.settings = settings or get_connector_settings()
        self._ncbi = ncbi or NCBIConnector(settings=self.settings)
        self._owns_ncbi = ncbi is None

    async def aclose(self) -> None:
        if self._owns_ncbi:
            await self._ncbi.aclose()

    async def __aenter__(self) -> "RefSeqConnector":
        return self

    async def __aexit__(self, *_exc: object) -> None:
        await self.aclose()

    async def search(self, term: str, *, db: str = "nuccore", retmax: int = 20, retstart: int = 0) -> SearchPage:
        constrained = f"({term}) AND refseq[filter]"
        return await self._ncbi.esearch(db, constrained, retmax=retmax, retstart=retstart)

    async def find(self, query: SourceQuery) -> SearchPage:
        """Standardised search constrained to the curated RefSeq subset."""
        page = await self._ncbi.find(query, extra_term="refseq[filter]")
        return retag_page(page, self.source)

    async def fetch_fasta(self, accession: str, *, db: str = "nuccore") -> RawRecord:
        content = await self._ncbi.efetch(db, accession, rettype="fasta", retmode="text")
        return RawRecord(source=self.source, accession=accession, fmt="fasta", content=content)

    async def fetch_flat_file(self, accession: str, *, db: str = "nuccore") -> RawRecord:
        content = await self._ncbi.efetch(db, accession, rettype="gb", retmode="text")
        return RawRecord(source=self.source, accession=accession, fmt="genbank", content=content)
