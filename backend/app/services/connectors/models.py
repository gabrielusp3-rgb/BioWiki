"""Lightweight, source-agnostic DTOs returned by connectors.

Connectors deliberately return raw payloads (text or parsed JSON) rather than
mapping to the database models — parsing/ingestion is a separate concern, keeping
the connector layer decoupled and reusable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class RawRecord:
    """A raw record retrieved from an external database."""

    source: str
    accession: str
    fmt: str  # e.g. "fasta", "genbank", "json", "embl", "xml"
    content: str | None = None
    data: dict[str, Any] | None = None
    retrieved_at: datetime = field(default_factory=_now)


@dataclass(frozen=True)
class SearchHit:
    """A single search result identifier plus optional summary payload."""

    source: str
    identifier: str
    title: str | None = None
    data: dict[str, Any] | None = None


@dataclass(frozen=True)
class SearchPage:
    """A page of search hits with an optional continuation cursor."""

    source: str
    hits: list[SearchHit]
    total: int | None = None
    next_cursor: str | None = None


@dataclass(frozen=True)
class SourceQuery:
    """Standardised query contract accepted by every connector's ``find()``.

    Criteria are combined with AND semantics. Each connector translates the
    fields it can honestly answer into its official API's query language and
    raises :class:`~app.services.connectors.errors.ConnectorQueryError` for
    criteria the source does not support — results are never approximated or
    invented.
    """

    #: Source accession / stable identifier (e.g. NM_000207, P01308, 4HHB).
    accession: str | None = None
    #: Scientific organism name (e.g. "Homo sapiens").
    organism: str | None = None
    #: Official gene symbol (e.g. INS, TP53).
    gene: str | None = None
    #: Broad sequence category understood by BIOWIKI: "dna", "rna", "protein".
    sequence_type: str | None = None
    #: Restrict to records linked to this PubMed article.
    pubmed_id: int | str | None = None
    #: Free-text term, passed through to the source's own search syntax.
    text: str | None = None
    #: Page size.
    limit: int = 25
    #: Opaque continuation cursor from a previous ``SearchPage.next_cursor``.
    cursor: str | None = None

    def has_criteria(self) -> bool:
        return any(
            value is not None and str(value).strip()
            for value in (
                self.accession,
                self.organism,
                self.gene,
                self.sequence_type,
                self.pubmed_id,
                self.text,
            )
        )


def retag_page(page: SearchPage, source: str) -> SearchPage:
    """Re-attribute a page produced by a delegate connector (e.g. NCBI serving
    GenBank/RefSeq) so callers always see the logical source they queried."""
    return SearchPage(
        source=source,
        hits=[
            SearchHit(source=source, identifier=h.identifier, title=h.title, data=h.data)
            for h in page.hits
        ],
        total=page.total,
        next_cursor=page.next_cursor,
    )
