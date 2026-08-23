"""RCSB PDB connector (data + search + FASTA).

Refs:
- Data API:   https://data.rcsb.org
- Search API: https://search.rcsb.org
"""

from __future__ import annotations

from typing import Any

from app.services.connectors.base import BaseConnector
from app.services.connectors.config import ConnectorSettings, get_connector_settings
from app.services.connectors.errors import ConnectorQueryError
from app.services.connectors.models import RawRecord, SearchHit, SearchPage, SourceQuery


def _attribute_node(attribute: str, operator: str, value: Any) -> dict[str, Any]:
    return {
        "type": "terminal",
        "service": "text",
        "parameters": {"attribute": attribute, "operator": operator, "value": value},
    }


class PDBConnector(BaseConnector):
    source = "pdb"

    def __init__(self, settings: ConnectorSettings | None = None, **kwargs: Any) -> None:
        settings = settings or get_connector_settings()
        super().__init__(
            base_url=settings.pdb_data_url,
            rate_per_second=settings.pdb_rate_per_second,
            settings=settings,
            **kwargs,
        )

    async def get_entry(self, pdb_id: str) -> dict[str, Any]:
        return await self.get_json(f"core/entry/{pdb_id.upper()}")

    async def get_polymer_entity(self, pdb_id: str, entity_id: str) -> dict[str, Any]:
        return await self.get_json(f"core/polymer_entity/{pdb_id.upper()}/{entity_id}")

    async def fetch_fasta(self, pdb_id: str) -> RawRecord:
        url = f"{self.settings.pdb_fasta_url}/{pdb_id.upper()}"
        content = await self.get_text(url, headers={"Accept": "text/plain"})
        return RawRecord(source=self.source, accession=pdb_id.upper(), fmt="fasta", content=content)

    async def search(self, query: str, *, start: int = 0, rows: int = 25) -> SearchPage:
        body = {
            "query": {
                "type": "terminal",
                "service": "full_text",
                "parameters": {"value": query},
            },
            "return_type": "entry",
            "request_options": {"paginate": {"start": start, "rows": rows}},
        }
        return await self._run_search(body)

    async def find(self, query: SourceQuery) -> SearchPage:
        """Standardised search via the official RCSB Search API attributes."""
        if query.sequence_type and query.sequence_type.lower() != "protein":
            raise ConnectorQueryError(
                "RCSB PDB stores macromolecular structures (protein-centric); "
                f"sequence type {query.sequence_type!r} is not available here.",
                source=self.source,
            )
        nodes: list[dict[str, Any]] = []
        if query.accession:
            nodes.append(_attribute_node("rcsb_id", "exact_match", query.accession.strip().upper()))
        if query.organism:
            nodes.append(
                _attribute_node(
                    "rcsb_entity_source_organism.taxonomy_lineage.name",
                    "exact_match",
                    query.organism.strip(),
                )
            )
        if query.gene:
            nodes.append(
                _attribute_node(
                    "rcsb_entity_source_organism.rcsb_gene_name.value",
                    "exact_match",
                    query.gene.strip().upper(),
                )
            )
        if query.pubmed_id is not None and str(query.pubmed_id).strip():
            nodes.append(
                _attribute_node(
                    "rcsb_primary_citation.pdbx_database_id_PubMed",
                    "equals",
                    int(str(query.pubmed_id).strip()),
                )
            )
        if query.text:
            nodes.append(
                {
                    "type": "terminal",
                    "service": "full_text",
                    "parameters": {"value": query.text.strip()},
                }
            )
        if not nodes:
            raise ConnectorQueryError(
                "Empty query: provide at least one criterion.", source=self.source
            )

        query_node: dict[str, Any] = (
            nodes[0]
            if len(nodes) == 1
            else {"type": "group", "logical_operator": "and", "nodes": nodes}
        )
        start = int(query.cursor) if query.cursor and query.cursor.isdigit() else 0
        body = {
            "query": query_node,
            "return_type": "entry",
            "request_options": {"paginate": {"start": start, "rows": query.limit}},
        }
        return await self._run_search(body)

    async def _run_search(self, body: dict[str, Any]) -> SearchPage:
        response = await self.request("POST", self.settings.pdb_search_url, json_body=body)
        # RCSB answers 204 (empty body) when no entry matches.
        if response.status_code == 204 or not response.text.strip():
            return SearchPage(source=self.source, hits=[], total=0, next_cursor=None)
        payload = response.json()
        paginate = body.get("request_options", {}).get("paginate", {})
        start = int(paginate.get("start", 0))
        rows = int(paginate.get("rows", 25))

        result_set = payload.get("result_set", []) if isinstance(payload, dict) else []
        total = payload.get("total_count") if isinstance(payload, dict) else None
        hits = [
            SearchHit(source=self.source, identifier=item.get("identifier", ""), data=item)
            for item in result_set
        ]
        next_cursor = None
        if total is not None and start + rows < total:
            next_cursor = str(start + rows)
        return SearchPage(source=self.source, hits=hits, total=total, next_cursor=next_cursor)
