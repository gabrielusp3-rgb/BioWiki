"""UniProt connector (UniProtKB REST API).

Ref: https://www.uniprot.org/help/api_queries
"""

from __future__ import annotations

import re
from typing import Any

from app.services.connectors.base import BaseConnector
from app.services.connectors.config import ConnectorSettings, get_connector_settings
from app.services.connectors.errors import ConnectorParseError, ConnectorQueryError
from app.services.connectors.models import RawRecord, SearchHit, SearchPage, SourceQuery

_NEXT_LINK_RE = re.compile(r'<([^>]+)>;\s*rel="next"')
_CURSOR_RE = re.compile(r"[?&]cursor=([^&]+)")


class UniProtConnector(BaseConnector):
    source = "uniprot"

    def __init__(self, settings: ConnectorSettings | None = None, **kwargs: Any) -> None:
        settings = settings or get_connector_settings()
        super().__init__(
            base_url=settings.uniprot_base_url,
            rate_per_second=settings.uniprot_rate_per_second,
            settings=settings,
            **kwargs,
        )

    async def get_entry_json(self, accession: str) -> dict[str, Any]:
        return await self.get_json(f"uniprotkb/{accession}.json")

    async def get_entry_fasta(self, accession: str) -> RawRecord:
        content = await self.get_text(f"uniprotkb/{accession}.fasta")
        return RawRecord(source=self.source, accession=accession, fmt="fasta", content=content)

    async def search(
        self,
        query: str,
        *,
        fields: list[str] | None = None,
        size: int = 25,
        cursor: str | None = None,
    ) -> SearchPage:
        params: dict[str, Any] = {"query": query, "format": "json", "size": size}
        if fields:
            params["fields"] = ",".join(fields)
        if cursor:
            params["cursor"] = cursor

        response = await self.request("GET", "uniprotkb/search", params=params)
        try:
            payload = response.json()
        except ValueError as exc:
            raise ConnectorParseError("Invalid UniProt search payload.", source=self.source) from exc

        results = payload.get("results", []) if isinstance(payload, dict) else []
        hits = [
            SearchHit(
                source=self.source,
                identifier=item.get("primaryAccession", ""),
                title=(item.get("proteinDescription", {})
                       .get("recommendedName", {})
                       .get("fullName", {})
                       .get("value")),
                data=item,
            )
            for item in results
        ]

        total = None
        total_header = response.headers.get("x-total-results")
        if total_header and total_header.isdigit():
            total = int(total_header)

        next_cursor = self._extract_next_cursor(response.headers.get("Link"))
        return SearchPage(source=self.source, hits=hits, total=total, next_cursor=next_cursor)

    async def find(self, query: SourceQuery) -> SearchPage:
        """Standardised search using official UniProtKB query fields
        (``accession:``, ``organism_name:``, ``gene:``, ``lit_pubmed:``)."""
        if query.sequence_type and query.sequence_type.lower() != "protein":
            raise ConnectorQueryError(
                "UniProtKB stores protein entries only; "
                f"sequence type {query.sequence_type!r} is not available here.",
                source=self.source,
            )
        parts: list[str] = []
        if query.accession:
            parts.append(f"accession:{query.accession.strip()}")
        if query.organism:
            parts.append(f'organism_name:"{query.organism.strip()}"')
        if query.gene:
            parts.append(f"gene:{query.gene.strip()}")
        if query.pubmed_id is not None and str(query.pubmed_id).strip():
            parts.append(f"lit_pubmed:{str(query.pubmed_id).strip()}")
        if query.text:
            parts.append(query.text.strip())
        if not parts:
            raise ConnectorQueryError(
                "Empty query: provide at least one criterion.", source=self.source
            )
        return await self.search(
            " AND ".join(parts), size=query.limit, cursor=query.cursor
        )

    @staticmethod
    def _extract_next_cursor(link_header: str | None) -> str | None:
        if not link_header:
            return None
        match = _NEXT_LINK_RE.search(link_header)
        if not match:
            return None
        cursor_match = _CURSOR_RE.search(match.group(1))
        return cursor_match.group(1) if cursor_match else None
