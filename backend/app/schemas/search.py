from __future__ import annotations

from app.schemas.common import CamelModel


class SearchResult(CamelModel):
    id: str
    accession: str
    title: str
    type: str
    organism: str
    source: str
    length: int
    category: str


class SearchPublication(CamelModel):
    id: str
    pubmed_id: int | None = None
    doi: str | None = None
    title: str
    authors: list[str] = []
    journal: str | None = None
    year: int | None = None
    url: str | None = None


class SearchPaleogenomicsProfile(CamelModel):
    id: str
    slug: str
    title: str
    scientific_name: str
    type: str = "paleogenomics"


class SearchResponse(CamelModel):
    query: str
    total: int
    results: list[SearchResult]
    next_cursor: str | None = None
    publications: list[SearchPublication] = []
    publications_total: int = 0
    paleogenomics_profiles: list[SearchPaleogenomicsProfile] = []


class SearchSuggestion(CamelModel):
    id: str
    label: str
    type: str
    accession: str | None = None
    slug: str | None = None


class SuggestResponse(CamelModel):
    query: str
    suggestions: list[SearchSuggestion]
