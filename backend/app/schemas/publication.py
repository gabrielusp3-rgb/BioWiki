from __future__ import annotations

import uuid

from app.schemas.common import CamelModel


class PublicationRead(CamelModel):
    id: uuid.UUID
    pubmed_id: int | None = None
    doi: str | None = None
    pmc_id: str | None = None
    title: str
    abstract: str | None = None
    authors: list[str] = []
    journal: str | None = None
    year: int | None = None
    volume: str | None = None
    pages: str | None = None
    url: str | None = None


class PublicationDetail(PublicationRead):
    sequence_accessions: list[str] = []
