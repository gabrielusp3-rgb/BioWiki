"""External database connectors.

Independent, decoupled, on-demand clients for recognised public databases.
Each connector shares a resilient async HTTP base (timeout, retry with backoff,
per-source rate limiting, typed errors) but is otherwise self-contained.

IMPORTANT: connectors never download data automatically. They expose read
operations (fetch/search) that callers invoke explicitly; there is no scheduler,
crawler or bulk ingestion here.
"""

from app.services.connectors.base import BaseConnector
from app.services.connectors.config import ConnectorSettings, get_connector_settings
from app.services.connectors.ena import ENAConnector
from app.services.connectors.ensembl import EnsemblConnector
from app.services.connectors.errors import (
    ConnectorError,
    ConnectorHTTPError,
    ConnectorNotFound,
    ConnectorParseError,
    ConnectorQueryError,
    ConnectorRateLimited,
    ConnectorTimeout,
    ConnectorUnavailable,
)
from app.services.connectors.datasets import NCBIDatasetsConnector
from app.services.connectors.genbank import GenBankConnector
from app.services.connectors.models import RawRecord, SearchHit, SearchPage, SourceQuery
from app.services.connectors.ncbi import NCBIConnector
from app.services.connectors.pdb import PDBConnector
from app.services.connectors.pubmed import PubMedArticle, PubMedConnector
from app.services.connectors.refseq import RefSeqConnector
from app.services.connectors.rfam import RfamConnector
from app.services.connectors.uniprot import UniProtConnector

__all__ = [
    "BaseConnector",
    "ConnectorSettings",
    "get_connector_settings",
    "NCBIConnector",
    "GenBankConnector",
    "RefSeqConnector",
    "UniProtConnector",
    "EnsemblConnector",
    "PDBConnector",
    "ENAConnector",
    "PubMedConnector",
    "PubMedArticle",
    "NCBIDatasetsConnector",
    "RfamConnector",
    "RawRecord",
    "SearchHit",
    "SearchPage",
    "SourceQuery",
    "ConnectorError",
    "ConnectorHTTPError",
    "ConnectorNotFound",
    "ConnectorParseError",
    "ConnectorQueryError",
    "ConnectorRateLimited",
    "ConnectorTimeout",
    "ConnectorUnavailable",
]
