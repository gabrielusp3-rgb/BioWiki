"""PubMed connector (NCBI E-utilities, ``db=pubmed``).

Retrieves real bibliographic records: title, authors, journal, year, DOI and
PMC ID. Reuses the shared NCBI E-utilities budget (tool/email/api key and the
same rate policy).

Ref: https://www.ncbi.nlm.nih.gov/books/NBK25501/
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Any

from app.services.connectors.base import BaseConnector
from app.services.connectors.config import ConnectorSettings, get_connector_settings
from app.services.connectors.errors import ConnectorParseError, ConnectorQueryError
from app.services.connectors.models import SearchHit, SearchPage, SourceQuery

_YEAR_RE = re.compile(r"\b(1[89]\d{2}|20\d{2}|2100)\b")


@dataclass
class PubMedArticle:
    pubmed_id: int
    title: str | None = None
    authors: list[str] = field(default_factory=list)
    journal: str | None = None
    year: int | None = None
    volume: str | None = None
    pages: str | None = None
    doi: str | None = None
    pmc_id: str | None = None
    #: Real abstract text from the PubMed record (EFetch); None when the
    #: article has no abstract at the source.
    abstract: str | None = None

    @property
    def url(self) -> str:
        return f"https://pubmed.ncbi.nlm.nih.gov/{self.pubmed_id}/"

    @property
    def source_url(self) -> str:
        """Canonical origin link for this bibliographic record."""
        return self.url


class PubMedConnector(BaseConnector):
    source = "pubmed"

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

    async def esearch(self, term: str, *, retmax: int = 20, retstart: int = 0) -> SearchPage:
        params = {
            **self._common_params(),
            "db": "pubmed",
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

        next_cursor = str(retstart + retmax) if retstart + retmax < total else None
        hits = [SearchHit(source=self.source, identifier=uid) for uid in ids]
        return SearchPage(source=self.source, hits=hits, total=total, next_cursor=next_cursor)

    async def find(self, query: SourceQuery) -> SearchPage:
        """Standardised literature search over PubMed.

        Every criterion maps to official PubMed search fields; no result is
        approximated. ``sequence_type`` is rejected because PubMed indexes
        literature, not sequences.
        """
        if query.sequence_type:
            raise ConnectorQueryError(
                "PubMed indexes bibliographic records, not sequences; "
                "sequence type filters are not applicable here.",
                source=self.source,
            )
        parts: list[str] = []
        if query.pubmed_id is not None and str(query.pubmed_id).strip():
            parts.append(f"{str(query.pubmed_id).strip()}[uid]")
        if query.accession:
            # Accession numbers cited in articles are indexed by PubMed as
            # Secondary Source IDs and in the general index.
            parts.append(f'"{query.accession.strip()}"')
        if query.organism:
            org = query.organism.strip()
            parts.append(f'("{org}"[MeSH Terms] OR "{org}"[Title/Abstract])')
        if query.gene:
            parts.append(f'"{query.gene.strip()}"[Title/Abstract]')
        if query.text:
            parts.append(query.text.strip())
        if not parts:
            raise ConnectorQueryError(
                "Empty query: provide at least one criterion.", source=self.source
            )
        offset = int(query.cursor) if query.cursor and query.cursor.isdigit() else 0
        return await self.esearch(" AND ".join(parts), retmax=query.limit, retstart=offset)

    async def fetch_abstracts(self, pmids: list[int | str]) -> dict[int, str]:
        """Real abstracts via EFetch XML; PMIDs without an abstract are absent."""
        if not pmids:
            return {}
        params = {
            **self._common_params(),
            "db": "pubmed",
            "id": ",".join(str(p) for p in pmids),
            "retmode": "xml",
        }
        raw = await self.get_text("efetch.fcgi", params=params)
        try:
            root = ET.fromstring(raw)
        except ET.ParseError as exc:
            raise ConnectorParseError("Unexpected EFetch XML payload.", source=self.source) from exc

        abstracts: dict[int, str] = {}
        for article in root.iter("PubmedArticle"):
            pmid_el = article.find(".//MedlineCitation/PMID")
            if pmid_el is None or not (pmid_el.text or "").strip():
                continue
            sections: list[str] = []
            for abstract_text in article.findall(".//Abstract/AbstractText"):
                text = "".join(abstract_text.itertext()).strip()
                if not text:
                    continue
                label = (abstract_text.get("Label") or "").strip()
                sections.append(f"{label}: {text}" if label else text)
            if sections:
                abstracts[int(pmid_el.text.strip())] = "\n\n".join(sections)
        return abstracts

    async def fetch_articles(
        self, pmids: list[int | str], *, with_abstracts: bool = False
    ) -> list[PubMedArticle]:
        """Fetch bibliographic summaries (ESummary JSON) for the given PMIDs."""
        if not pmids:
            return []
        params = {
            **self._common_params(),
            "db": "pubmed",
            "id": ",".join(str(p) for p in pmids),
            "retmode": "json",
        }
        payload = await self.get_json("esummary.fcgi", params=params)
        try:
            result = payload["result"]
            uids = result.get("uids", [])
        except (KeyError, TypeError) as exc:
            raise ConnectorParseError("Unexpected ESummary payload.", source=self.source) from exc

        articles: list[PubMedArticle] = []
        for uid in uids:
            doc = result.get(uid)
            if not isinstance(doc, dict):
                continue
            articles.append(self._parse_summary(uid, doc))

        if with_abstracts and articles:
            abstracts = await self.fetch_abstracts([a.pubmed_id for a in articles])
            for article in articles:
                article.abstract = abstracts.get(article.pubmed_id)
        return articles

    @staticmethod
    def _parse_summary(uid: str, doc: dict[str, Any]) -> PubMedArticle:
        authors = [
            a.get("name", "").strip()
            for a in doc.get("authors", [])
            if isinstance(a, dict) and a.get("name")
        ]

        year: int | None = None
        year_match = _YEAR_RE.search(str(doc.get("pubdate", "")))
        if year_match:
            year = int(year_match.group(1))

        doi = pmc_id = None
        for article_id in doc.get("articleids", []):
            if not isinstance(article_id, dict):
                continue
            id_type = article_id.get("idtype")
            value = str(article_id.get("value", "")).strip()
            if id_type == "doi" and value:
                doi = value
            elif id_type == "pmc" and value:
                pmc_id = value

        return PubMedArticle(
            pubmed_id=int(uid),
            title=(doc.get("title") or "").strip().rstrip(".") or None,
            authors=authors,
            journal=(doc.get("fulljournalname") or doc.get("source") or "").strip() or None,
            year=year,
            volume=(doc.get("volume") or "").strip() or None,
            pages=(doc.get("pages") or "").strip() or None,
            doi=doi,
            pmc_id=pmc_id,
        )
