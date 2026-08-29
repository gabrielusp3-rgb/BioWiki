"""NCBI Entrez E-utilities connector.

Thin, on-demand client over ESearch / ESummary / EFetch. It powers the GenBank
and RefSeq connectors too (both are served by NCBI). No bulk downloading or
scheduling is performed here — callers request one operation at a time.

Ref: https://www.ncbi.nlm.nih.gov/books/NBK25501/
"""

from __future__ import annotations

from typing import Any

from app.services.connectors.base import BaseConnector
from app.services.connectors.config import ConnectorSettings, get_connector_settings
from app.services.connectors.errors import ConnectorParseError, ConnectorQueryError
from app.services.connectors.models import RawRecord, SearchHit, SearchPage, SourceQuery

# Documented Entrez "biomol" property filters (not invented — see the NCBI
# nucleotide properties index).
_RNA_PROP_CLAUSE = (
    '("biomol mrna"[PROP] OR "biomol rrna"[PROP] OR "biomol trna"[PROP]'
    ' OR "biomol ncrna"[PROP] OR "biomol crna"[PROP])'
)
_DNA_PROP_CLAUSE = '"biomol genomic"[PROP]'


def entrez_db_for(sequence_type: str | None) -> str:
    """Pick the Entrez database for a BIOWIKI sequence category."""
    if sequence_type and sequence_type.lower() == "protein":
        return "protein"
    return "nuccore"


def build_entrez_term(query: SourceQuery) -> str:
    """Translate a :class:`SourceQuery` into official Entrez search syntax."""
    parts: list[str] = []
    if query.accession:
        parts.append(f"{query.accession.strip()}[ACCN]")
    if query.organism:
        parts.append(f'"{query.organism.strip()}"[ORGN]')
    if query.gene:
        parts.append(f"{query.gene.strip()}[GENE]")
    if query.sequence_type:
        st = query.sequence_type.lower()
        if st == "dna":
            parts.append(_DNA_PROP_CLAUSE)
        elif st == "rna":
            parts.append(_RNA_PROP_CLAUSE)
        elif st != "protein":
            raise ConnectorQueryError(
                f"Unsupported sequence type {query.sequence_type!r} for Entrez.",
                source="ncbi",
            )
    if query.text:
        parts.append(query.text.strip())
    if not parts:
        raise ConnectorQueryError("Empty query: provide at least one criterion.", source="ncbi")
    return " AND ".join(parts)


class NCBIConnector(BaseConnector):
    source = "ncbi"

    def __init__(self, settings: ConnectorSettings | None = None, **kwargs: Any) -> None:
        settings = settings or get_connector_settings()
        super().__init__(
            base_url=settings.ncbi_base_url,
            rate_per_second=settings.ncbi_effective_rate,
            settings=settings,
            **kwargs,
        )

    def _common_params(self) -> dict[str, Any]:
        params: dict[str, Any] = {"tool": self.settings.ncbi_tool}
        if self.settings.ncbi_email:
            params["email"] = self.settings.ncbi_email
        if self.settings.ncbi_api_key:
            params["api_key"] = self.settings.ncbi_api_key
        return params

    async def esearch(
        self,
        db: str,
        term: str,
        *,
        retmax: int = 20,
        retstart: int = 0,
    ) -> SearchPage:
        """Search a database, returning matching UIDs."""
        params = {
            **self._common_params(),
            "db": db,
            "term": term,
            "retmode": "json",
            "retmax": retmax,
            "retstart": retstart,
        }
        payload = await self.get_json("esearch.fcgi", params=params)
        try:
            result = payload["esearchresult"]
            ids = result.get("idlist", [])
            total = int(result.get("count", len(ids)))
        except (KeyError, TypeError, ValueError) as exc:
            raise ConnectorParseError("Unexpected ESearch payload.", source=self.source) from exc

        next_cursor = None
        if retstart + retmax < total:
            next_cursor = str(retstart + retmax)
        hits = [SearchHit(source=self.source, identifier=uid) for uid in ids]
        return SearchPage(source=self.source, hits=hits, total=total, next_cursor=next_cursor)

    async def epost(self, db: str, ids: list[str]) -> tuple[str, str]:
        """Upload UIDs/accessions into the Entrez History server (EPost).

        Returns ``(webenv, query_key)`` for subsequent ESummary/EFetch calls.
        """
        from urllib.parse import urlencode
        import xml.etree.ElementTree as ET

        if not ids:
            raise ConnectorQueryError("EPost requires at least one identifier.", source=self.source)
        params = {**self._common_params(), "db": db}
        body = urlencode({"id": ",".join(ids)})
        response = await self.request(
            "POST",
            "epost.fcgi",
            params=params,
            content=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        try:
            root = ET.fromstring(response.text)
        except ET.ParseError as exc:
            raise ConnectorParseError("Unexpected EPost XML payload.", source=self.source) from exc
        webenv = root.findtext("WebEnv")
        query_key = root.findtext("QueryKey")
        if not webenv or not query_key:
            raise ConnectorParseError("EPost response missing WebEnv/QueryKey.", source=self.source)
        return webenv, query_key

    async def esummary(
        self,
        db: str,
        ids: list[str] | None = None,
        *,
        webenv: str | None = None,
        query_key: str | None = None,
        retstart: int = 0,
        retmax: int = 500,
    ) -> dict[str, Any]:
        """Fetch document summaries for UIDs or an Entrez History set."""
        params: dict[str, Any] = {
            **self._common_params(),
            "db": db,
            "retmode": "json",
            "retstart": retstart,
            "retmax": retmax,
        }
        if webenv and query_key:
            params["WebEnv"] = webenv
            params["query_key"] = query_key
        elif ids:
            params["id"] = ",".join(ids)
        else:
            raise ConnectorQueryError(
                "ESummary requires identifiers or a WebEnv/query_key pair.",
                source=self.source,
            )
        return await self.get_json("esummary.fcgi", params=params)

    async def efetch(
        self,
        db: str,
        ids: list[str] | str,
        *,
        rettype: str = "fasta",
        retmode: str = "text",
    ) -> str:
        """Fetch full records as raw text (FASTA, GenBank flat file, XML…)."""
        id_value = ids if isinstance(ids, str) else ",".join(ids)
        params = {
            **self._common_params(),
            "db": db,
            "id": id_value,
            "rettype": rettype,
            "retmode": retmode,
        }
        return await self.get_text("efetch.fcgi", params=params)

    async def fetch_fasta(self, db: str, accession: str) -> RawRecord:
        content = await self.efetch(db, accession, rettype="fasta", retmode="text")
        return RawRecord(source=self.source, accession=accession, fmt="fasta", content=content)

    async def elink(self, dbfrom: str, db: str, ids: list[str] | str) -> list[str]:
        """ELink: UIDs in ``db`` linked to the given UIDs in ``dbfrom``
        (e.g. sequences cited by a PubMed article)."""
        id_value = ids if isinstance(ids, str) else ",".join(ids)
        params = {
            **self._common_params(),
            "dbfrom": dbfrom,
            "db": db,
            "id": id_value,
            "retmode": "json",
        }
        payload = await self.get_json("elink.fcgi", params=params)
        linked: list[str] = []
        try:
            for linkset in payload.get("linksets", []):
                for linksetdb in linkset.get("linksetdbs", []):
                    linked.extend(str(uid) for uid in linksetdb.get("links", []))
        except (AttributeError, TypeError) as exc:
            raise ConnectorParseError("Unexpected ELink payload.", source=self.source) from exc
        # Preserve order, drop duplicates across linkset groups.
        return list(dict.fromkeys(linked))

    async def find(self, query: SourceQuery, *, extra_term: str | None = None) -> SearchPage:
        """Standardised search over Entrez (see :class:`SourceQuery`).

        ``pubmed_id`` is resolved through ELink (real citation links registered
        at NCBI); every other criterion is translated to Entrez search syntax.
        """
        db = entrez_db_for(query.sequence_type)
        offset = int(query.cursor) if query.cursor and query.cursor.isdigit() else 0

        if query.pubmed_id is not None and str(query.pubmed_id).strip():
            linked = await self.elink("pubmed", db, str(query.pubmed_id).strip())
            if extra_term and linked:
                # Keep only linked UIDs that also satisfy the constraint
                # (e.g. RefSeq subset) — verified against Entrez, not guessed.
                uid_clause = " OR ".join(f"{uid}[UID]" for uid in linked[:200])
                constrained = await self.esearch(
                    db, f"({uid_clause}) AND {extra_term}", retmax=200
                )
                allowed = {hit.identifier for hit in constrained.hits}
                linked = [uid for uid in linked if uid in allowed]
            window = linked[offset : offset + query.limit]
            next_cursor = str(offset + query.limit) if offset + query.limit < len(linked) else None
            hits = [SearchHit(source=self.source, identifier=uid) for uid in window]
            return SearchPage(
                source=self.source, hits=hits, total=len(linked), next_cursor=next_cursor
            )

        term = build_entrez_term(query)
        if extra_term:
            term = f"({term}) AND {extra_term}"
        return await self.esearch(db, term, retmax=query.limit, retstart=offset)
