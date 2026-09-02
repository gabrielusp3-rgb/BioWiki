"""NCBI Datasets v2 connector (genome assembly reports).

Ref: https://www.ncbi.nlm.nih.gov/datasets/docs/v2/reference-docs/rest-api/
"""

from __future__ import annotations

from typing import Any

from app.services.connectors.base import BaseConnector
from app.services.connectors.config import ConnectorSettings, get_connector_settings
from app.services.connectors.errors import ConnectorParseError


class NCBIDatasetsConnector(BaseConnector):
    source = "ncbi_datasets"

    def __init__(self, settings: ConnectorSettings | None = None, **kwargs: Any) -> None:
        settings = settings or get_connector_settings()
        headers = {}
        if settings.ncbi_api_key:
            headers["api-key"] = settings.ncbi_api_key
        super().__init__(
            base_url=settings.datasets_base_url,
            rate_per_second=settings.datasets_rate_per_second,
            settings=settings,
            default_headers=headers or None,
            **kwargs,
        )

    async def assembly_reports(self, accessions: list[str]) -> list[dict[str, Any]]:
        """Dataset reports for specific assembly accessions (GCF_/GCA_)."""
        if not accessions:
            return []
        joined = ",".join(a.strip() for a in accessions if a.strip())
        payload = await self.get_json(f"genome/accession/{joined}/dataset_report")
        return self._extract_reports(payload)

    async def assemblies_for_taxon(
        self, taxon: str, *, page_size: int = 20, page_token: str | None = None
    ) -> tuple[list[dict[str, Any]], str | None]:
        """Dataset reports for a taxon (name or tax ID), paginated."""
        params: dict[str, Any] = {"page_size": page_size}
        if page_token:
            params["page_token"] = page_token
        payload = await self.get_json(f"genome/taxon/{taxon}/dataset_report", params=params)
        reports = self._extract_reports(payload)
        next_token = payload.get("next_page_token") if isinstance(payload, dict) else None
        return reports, next_token or None

    async def taxonomy_reports(self, tax_ids: list[int | str]) -> list[dict[str, Any]]:
        """NCBI Datasets taxonomy metadata for numeric TaxIDs or names."""
        return await self._taxonomy_payload(tax_ids, suffix="")

    async def taxonomy_name_reports(self, tax_ids: list[int | str]) -> list[dict[str, Any]]:
        """NCBI Datasets taxonomy names report (accepted name + synonyms)."""
        return await self._taxonomy_payload(tax_ids, suffix="/name_report")

    async def _taxonomy_payload(self, taxons: list[int | str], *, suffix: str) -> list[dict[str, Any]]:
        ids = [str(t).strip() for t in taxons if str(t).strip()]
        if not ids:
            return []
        joined = ",".join(ids)
        payload = await self.get_json(f"taxonomy/taxon/{joined}{suffix}")
        if not isinstance(payload, dict):
            raise ConnectorParseError("Unexpected Datasets taxonomy payload.", source=self.source)
        nodes = payload.get("taxonomy_nodes") or payload.get("reports") or []
        return [n for n in nodes if isinstance(n, dict)]

    def _extract_reports(self, payload: Any) -> list[dict[str, Any]]:
        if not isinstance(payload, dict):
            raise ConnectorParseError("Unexpected Datasets payload.", source=self.source)
        reports = payload.get("reports", [])
        return [r for r in reports if isinstance(r, dict)]
