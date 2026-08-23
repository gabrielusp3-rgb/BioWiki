"""EMBL-EBI ENA connector (Browser + Portal APIs).

Refs:
- Browser API: https://www.ebi.ac.uk/ena/browser/api
- Portal API:  https://www.ebi.ac.uk/ena/portal/api
"""

from __future__ import annotations

from typing import Any

from app.services.connectors.base import BaseConnector
from app.services.connectors.config import ConnectorSettings, get_connector_settings
from app.services.connectors.errors import ConnectorParseError, ConnectorQueryError
from app.services.connectors.models import RawRecord, SearchHit, SearchPage, SourceQuery

_TEXT_FORMATS = {"fasta", "embl"}


class ENAConnector(BaseConnector):
    source = "ena"

    def __init__(self, settings: ConnectorSettings | None = None, **kwargs: Any) -> None:
        settings = settings or get_connector_settings()
        super().__init__(
            base_url=settings.ena_browser_url,
            rate_per_second=settings.ena_rate_per_second,
            settings=settings,
            **kwargs,
        )

    async def fetch_record(self, accession: str, *, fmt: str = "fasta") -> RawRecord:
        """Fetch a record from the ENA Browser API (fasta | embl | xml)."""
        fmt = fmt.lower()
        content = await self.get_text(
            f"{fmt}/{accession}",
            params={"download": "false"},
            headers={"Accept": "text/plain" if fmt in _TEXT_FORMATS else "application/xml"},
        )
        return RawRecord(source=self.source, accession=accession, fmt=fmt, content=content)

    async def search(
        self,
        query: str,
        *,
        result: str = "sequence",
        fields: list[str] | None = None,
        limit: int = 25,
        offset: int = 0,
    ) -> SearchPage:
        """Search via the ENA Portal API."""
        params: dict[str, Any] = {
            "result": result,
            "query": query,
            "format": "json",
            "limit": limit,
            "offset": offset,
        }
        if fields:
            params["fields"] = ",".join(fields)

        url = f"{self.settings.ena_portal_url}/search"
        response = await self.request("GET", url, params=params)
        text = response.text.strip()
        if not text:
            return SearchPage(source=self.source, hits=[], total=0, next_cursor=None)
        try:
            payload = response.json()
        except ValueError as exc:
            raise ConnectorParseError("Invalid ENA search payload.", source=self.source) from exc

        rows = payload if isinstance(payload, list) else []
        hits = [
            SearchHit(
                source=self.source,
                identifier=item.get("accession") or item.get("sequence_accession") or "",
                data=item,
            )
            for item in rows
        ]
        next_cursor = str(offset + limit) if len(rows) == limit else None
        return SearchPage(source=self.source, hits=hits, total=None, next_cursor=next_cursor)

    async def summary(self, accession: str) -> dict[str, Any]:
        """Record summary from the ENA Browser API (real metadata, including
        molecule type, taxon and linked publications)."""
        return await self.get_json(f"summary/{accession.strip()}")

    async def find(self, query: SourceQuery) -> SearchPage:
        """Standardised search.

        Accession lookups go through the ENA Browser summary endpoint (the
        Portal API does not query by accession); everything else uses the
        Portal query language (``tax_name()``, ``description=`` over real
        annotations).
        """
        if query.sequence_type and query.sequence_type.lower() == "protein":
            raise ConnectorQueryError(
                "The ENA sequence result set holds nucleotide records; "
                "use the UniProt or PDB connector for proteins.",
                source=self.source,
            )
        if query.pubmed_id is not None and str(query.pubmed_id).strip():
            raise ConnectorQueryError(
                "The ENA Portal API does not index records by PubMed ID; "
                "use the NCBI connector for citation-based search.",
                source=self.source,
            )

        if query.accession:
            payload = await self.summary(query.accession.strip())
            summaries = payload.get("summaries", []) if isinstance(payload, dict) else []
            hits = [
                SearchHit(
                    source=self.source,
                    identifier=item.get("accession", ""),
                    title=item.get("description"),
                    data=item,
                )
                for item in summaries
                if isinstance(item, dict)
            ]
            return SearchPage(
                source=self.source, hits=hits, total=len(hits), next_cursor=None
            )

        parts: list[str] = []
        if query.organism:
            parts.append(f'tax_name("{query.organism.strip()}")')
        if query.gene:
            # Matches the gene symbol inside the record's real description line.
            parts.append(f'description="*{query.gene.strip()}*"')
        if query.text:
            parts.append(f'description="*{query.text.strip()}*"')
        if not parts:
            raise ConnectorQueryError(
                "Empty query: provide at least one criterion.", source=self.source
            )

        offset = int(query.cursor) if query.cursor and query.cursor.isdigit() else 0
        return await self.search(
            " AND ".join(parts),
            result="sequence",
            fields=["accession", "description", "scientific_name", "tax_id", "base_count"],
            limit=query.limit,
            offset=offset,
        )
