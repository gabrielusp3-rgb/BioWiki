"""Connector settings (base URLs, credentials, rate/retry/timeout budgets).

Kept separate from the application settings so the connector layer stays
decoupled and independently configurable.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ConnectorSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="CONNECTOR_",
        extra="ignore",
    )

    # Shared HTTP budgets
    timeout_seconds: float = Field(default=90.0)
    max_retries: int = Field(default=3)
    backoff_base_seconds: float = Field(default=0.5)
    backoff_max_seconds: float = Field(default=8.0)
    user_agent: str = Field(default="BIOWIKI-Connector/0.1 (+https://biowiki.org)")

    # NCBI E-utilities (also serves GenBank and RefSeq)
    ncbi_base_url: str = Field(default="https://eutils.ncbi.nlm.nih.gov/entrez/eutils")
    ncbi_api_key: str = Field(default="")
    ncbi_tool: str = Field(default="biowiki")
    ncbi_email: str = Field(default="")
    # 3 req/s anonymous, 10 req/s with an API key (NCBI policy).
    ncbi_rate_per_second: float = Field(default=0.0)  # 0 => auto from api key

    # UniProt
    uniprot_base_url: str = Field(default="https://rest.uniprot.org")
    uniprot_rate_per_second: float = Field(default=10.0)

    # Ensembl REST
    ensembl_base_url: str = Field(default="https://rest.ensembl.org")
    ensembl_rate_per_second: float = Field(default=15.0)

    # RCSB PDB
    pdb_data_url: str = Field(default="https://data.rcsb.org/rest/v1")
    pdb_search_url: str = Field(default="https://search.rcsb.org/rcsbsearch/v2/query")
    pdb_fasta_url: str = Field(default="https://www.rcsb.org/fasta/entry")
    pdb_rate_per_second: float = Field(default=10.0)

    # EMBL-EBI ENA
    ena_browser_url: str = Field(default="https://www.ebi.ac.uk/ena/browser/api")
    ena_portal_url: str = Field(default="https://www.ebi.ac.uk/ena/portal/api")
    ena_rate_per_second: float = Field(default=10.0)

    # NCBI Datasets v2 (genome assemblies)
    datasets_base_url: str = Field(default="https://api.ncbi.nlm.nih.gov/datasets/v2alpha")
    datasets_rate_per_second: float = Field(default=5.0)

    # Rfam (RNA families)
    rfam_base_url: str = Field(default="https://rfam.org")
    rfam_rate_per_second: float = Field(default=5.0)

    @property
    def ncbi_effective_rate(self) -> float:
        if self.ncbi_rate_per_second and self.ncbi_rate_per_second > 0:
            return self.ncbi_rate_per_second
        return 10.0 if self.ncbi_api_key else 3.0


@lru_cache
def get_connector_settings() -> ConnectorSettings:
    return ConnectorSettings()
