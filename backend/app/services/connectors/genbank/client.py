"""GenBank connector.

GenBank nucleotide/protein records are served by NCBI E-utilities. This
connector composes an :class:`NCBIConnector` (dependency injection) so it stays
decoupled while reusing the resilient E-utilities client.
"""

from __future__ import annotations

from typing import Any

from app.services.connectors.config import ConnectorSettings, get_connector_settings
from app.services.connectors.models import RawRecord, SearchPage, SourceQuery, retag_page
from app.services.connectors.ncbi.client import NCBIConnector


class GenBankConnector:
    source = "genbank"

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

    async def __aenter__(self) -> "GenBankConnector":
        return self

    async def __aexit__(self, *_exc: object) -> None:
        await self.aclose()

    async def search(self, term: str, *, db: str = "nuccore", retmax: int = 20, retstart: int = 0) -> SearchPage:
        return await self._ncbi.esearch(db, term, retmax=retmax, retstart=retstart)

    async def find(self, query: SourceQuery) -> SearchPage:
        """Standardised search (accession/organism/gene/type/PubMed ID) over
        GenBank via Entrez; results are re-attributed to this source."""
        page = await self._ncbi.find(query)
        return retag_page(page, self.source)

    async def fetch_flat_file(self, accession: str, *, db: str = "nuccore") -> RawRecord:
        """Fetch the GenBank flat file (.gb) for a nucleotide accession."""
        content = await self._ncbi.efetch(db, accession, rettype="gb", retmode="text")
        return RawRecord(source=self.source, accession=accession, fmt="genbank", content=content)

    async def fetch_fasta(self, accession: str, *, db: str = "nuccore") -> RawRecord:
        content = await self._ncbi.efetch(db, accession, rettype="fasta", retmode="text")
        return RawRecord(source=self.source, accession=accession, fmt="fasta", content=content)

    async def summary(self, ids: list[str], *, db: str = "nuccore") -> dict[str, Any]:
        return await self._ncbi.esummary(db, ids)
