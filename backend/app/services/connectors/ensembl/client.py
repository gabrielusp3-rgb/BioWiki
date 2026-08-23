"""Ensembl REST connector.

Ref: https://rest.ensembl.org
"""

from __future__ import annotations

from typing import Any

from app.services.connectors.base import BaseConnector
from app.services.connectors.config import ConnectorSettings, get_connector_settings
from app.services.connectors.errors import ConnectorNotFound, ConnectorQueryError
from app.services.connectors.models import RawRecord, SearchHit, SearchPage, SourceQuery


class EnsemblConnector(BaseConnector):
    source = "ensembl"

    def __init__(self, settings: ConnectorSettings | None = None, **kwargs: Any) -> None:
        settings = settings or get_connector_settings()
        super().__init__(
            base_url=settings.ensembl_base_url,
            rate_per_second=settings.ensembl_rate_per_second,
            settings=settings,
            **kwargs,
        )

    async def lookup_id(self, stable_id: str, *, expand: bool = False) -> dict[str, Any]:
        params = {"expand": 1 if expand else 0}
        return await self.get_json(f"lookup/id/{stable_id}", params=params)

    async def lookup_symbol(self, species: str, symbol: str, *, expand: bool = False) -> dict[str, Any]:
        params = {"expand": 1 if expand else 0}
        return await self.get_json(f"lookup/symbol/{species}/{symbol}", params=params)

    async def sequence_id(self, stable_id: str, *, seq_type: str = "genomic") -> RawRecord:
        """Fetch a sequence (genomic | cds | cdna | protein) as FASTA."""
        content = await self.get_text(
            f"sequence/id/{stable_id}",
            params={"type": seq_type},
            headers={"Accept": "text/x-fasta"},
        )
        return RawRecord(source=self.source, accession=stable_id, fmt="fasta", content=content)

    async def xrefs_id(self, stable_id: str) -> list[dict[str, Any]]:
        return await self.get_json(f"xrefs/id/{stable_id}")

    async def find(self, query: SourceQuery) -> SearchPage:
        """Standardised lookup over the Ensembl REST API.

        Ensembl exposes exact lookups, not free-text search: supported queries
        are *accession* (stable ID) and *gene symbol + organism*. Anything else
        raises :class:`ConnectorQueryError` — nothing is approximated.
        """
        if query.pubmed_id is not None and str(query.pubmed_id).strip():
            raise ConnectorQueryError(
                "Ensembl REST does not index records by PubMed ID; "
                "use the NCBI or UniProt connector for citation-based search.",
                source=self.source,
            )

        try:
            if query.accession:
                data = await self.lookup_id(query.accession.strip())
            elif query.gene and query.organism:
                species = query.organism.strip().lower().replace(" ", "_")
                data = await self.lookup_symbol(species, query.gene.strip())
            else:
                raise ConnectorQueryError(
                    "Ensembl supports lookup by stable ID (accession) or by "
                    "gene symbol combined with organism.",
                    source=self.source,
                )
        except ConnectorNotFound:
            return SearchPage(source=self.source, hits=[], total=0, next_cursor=None)

        hit = SearchHit(
            source=self.source,
            identifier=str(data.get("id") or query.accession or ""),
            title=data.get("display_name") or data.get("description"),
            data=data,
        )
        return SearchPage(source=self.source, hits=[hit], total=1, next_cursor=None)
