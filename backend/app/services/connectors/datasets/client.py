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

    def _extract_reports(self, payload: Any) -> list[dict[str, Any]]:
        if not isinstance(payload, dict):
            raise ConnectorParseError("Unexpected Datasets payload.", source=self.source)
        reports = payload.get("reports", [])
        return [r for r in reports if isinstance(r, dict)]
