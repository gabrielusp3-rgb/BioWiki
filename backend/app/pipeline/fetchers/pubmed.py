"""PubMed fetcher: real bibliographic records and sequence↔article links.

Two operations:
- ``ingest_pmids``: fetch and persist publications by PubMed ID (also backfills
  publications previously created from partial GenBank references).
- ``link_sequence``: attach PubMed articles to an already-ingested sequence —
  and therefore, transitively, to its organism, gene and protein context.
"""

from __future__ import annotations

from sqlalchemy import select

from app.database.session import get_sessionmaker
from app.models.publication import Publication, SequenceReference
from app.models.sequence import Sequence
from app.pipeline.fetchers.base import chunked
from app.pipeline.importers.publication_importer import upsert_publication
from app.pipeline.logging import get_logger
from app.pipeline.models import ImportReport, ParsedPublication
from app.pipeline.run_log import record_run
from app.services.connectors.pubmed import PubMedArticle, PubMedConnector

logger = get_logger("biowiki.pipeline.fetchers.pubmed")

_FETCH_CHUNK = 100


def _article_to_parsed(article: PubMedArticle) -> ParsedPublication:
    return ParsedPublication(
        title=article.title,
        pubmed_id=article.pubmed_id,
        doi=article.doi,
        pmc_id=article.pmc_id,
        abstract=article.abstract,
        authors=article.authors,
        journal=article.journal,
        year=article.year,
        volume=article.volume,
        pages=article.pages,
        url=article.url,
    )


async def fetch_articles(
    pmids: list[int | str],
    *,
    connector: PubMedConnector | None = None,
) -> list[PubMedArticle]:
    owns = connector is None
    conn = connector or PubMedConnector()
    articles: list[PubMedArticle] = []
    try:
        unique = list(dict.fromkeys(str(p).strip() for p in pmids if str(p).strip()))
        for start in range(0, len(unique), _FETCH_CHUNK):
            chunk = unique[start : start + _FETCH_CHUNK]
            articles.extend(await conn.fetch_articles(chunk, with_abstracts=True))
    finally:
        if owns:
            await conn.aclose()
    logger.info("pubmed fetch: %d article(s) retrieved", len(articles))
    return articles


async def ingest_pmids(pmids: list[int | str]) -> ImportReport:
    """Persist real PubMed records (upsert by PMID)."""
    articles = await fetch_articles(pmids)

    async with record_run("pubmed", "fetch_pmids", {"pmids": [str(p) for p in pmids]}) as run:
        report = ImportReport()
        async with get_sessionmaker()() as session:
            for article in articles:
                report.total += 1
                try:
                    async with session.begin_nested():
                        existed = (
                            await session.execute(
                                select(Publication.id).where(
                                    Publication.pubmed_id == article.pubmed_id
                                )
                            )
                        ).scalar_one_or_none()
                        publication = await upsert_publication(
                            session, _article_to_parsed(article)
                        )
                    if publication is None:
                        report.skipped += 1
                        report.errors.append(f"skip PMID {article.pubmed_id}: no title at source")
                    elif existed is None:
                        report.created += 1
                    else:
                        report.updated += 1
                except Exception as exc:  # noqa: BLE001 — isolate per-record failures
                    report.failed += 1
                    report.errors.append(f"fail PMID {article.pubmed_id}: {exc}")
                    logger.exception("fail PMID %s", article.pubmed_id)
            await session.commit()
        run.set_report(report)

    logger.info("pubmed import finished: %s", report.as_dict())
    return report


async def link_sequence(accession: str, pmids: list[int | str]) -> ImportReport:
    """Attach PubMed articles to an existing sequence record (additive)."""
    articles = await fetch_articles(pmids)

    async with record_run(
        "pubmed", "link_sequence", {"accession": accession, "pmids": [str(p) for p in pmids]}
    ) as run:
        report = ImportReport()
        async with get_sessionmaker()() as session:
            sequence = (
                await session.execute(
                    select(Sequence).where(Sequence.accession == accession)
                )
            ).scalars().first()
            if sequence is None:
                report.errors.append(f"sequence {accession} not found; ingest it first")
                run.set_report(report)
                await session.commit()
                logger.warning("pubmed link: sequence %s not found", accession)
                return report

            for article in articles:
                report.total += 1
                try:
                    async with session.begin_nested():
                        publication = await upsert_publication(
                            session, _article_to_parsed(article)
                        )
                        if publication is None:
                            report.skipped += 1
                            continue
                        existing_link = (
                            await session.execute(
                                select(SequenceReference).where(
                                    SequenceReference.sequence_id == sequence.id,
                                    SequenceReference.publication_id == publication.id,
                                )
                            )
                        ).scalar_one_or_none()
                        if existing_link is None:
                            session.add(
                                SequenceReference(
                                    sequence_id=sequence.id,
                                    publication_id=publication.id,
                                )
                            )
                            report.created += 1
                        else:
                            report.updated += 1
                except Exception as exc:  # noqa: BLE001
                    report.failed += 1
                    report.errors.append(f"fail PMID {article.pubmed_id}: {exc}")
                    logger.exception("fail PMID %s", article.pubmed_id)
            await session.commit()
        run.set_report(report)

    logger.info("pubmed link finished: %s", report.as_dict())
    return report


async def ingest_search(
    term: str,
    *,
    limit: int = 200,
    retstart: int = 0,
) -> ImportReport:
    """Search PubMed with a real Entrez term and persist matching articles."""
    owns = True
    conn = PubMedConnector()
    try:
        page = await conn.esearch(term, retmax=max(1, min(limit, 500)), retstart=retstart)
        pmids = [hit.identifier for hit in page.hits if hit.identifier]
    finally:
        if owns:
            await conn.aclose()

    if not pmids:
        logger.info("pubmed search: no hits for term=%r retstart=%s", term, retstart)
        return ImportReport()

    async with get_sessionmaker()() as session:
        existing = set(
            (
                await session.execute(
                    select(Publication.pubmed_id).where(
                        Publication.pubmed_id.in_(
                            [int(p) for p in pmids if str(p).isdigit()]
                        )
                    )
                )
            )
            .scalars()
            .all()
        )

    new_pmids = [p for p in pmids if int(p) not in existing]
    skipped_known = len(pmids) - len(new_pmids)
    if not new_pmids:
        report = ImportReport()
        report.total = len(pmids)
        report.updated = skipped_known
        logger.info("pubmed search: all %d PMID(s) already stored", len(pmids))
        return report

    report = await ingest_pmids(new_pmids)
    report.updated += skipped_known
    report.total += skipped_known
    return report


async def ingest_elinks(
    accessions: list[str],
    *,
    dbfrom: str = "nuccore",
    max_pmids: int = 2000,
) -> ImportReport:
    """Import PubMed records that NCBI ELink reports for the given accessions.

    Only bibliographic records are stored here. Per-sequence citation links
    remain those already present on the source records (GenBank REFERENCE /
    UniProt citations). Batched ELink flattens IDs, so this function does not
    invent sequence↔article rows from the mixed link set.
    """
    from app.services.connectors.ncbi import NCBIConnector

    unique = list(dict.fromkeys(a.strip() for a in accessions if a and a.strip()))
    if not unique:
        return ImportReport()

    linked: list[str] = []
    async with NCBIConnector() as conn:
        for group in chunked(unique, 40):
            try:
                linked.extend(await conn.elink(dbfrom, "pubmed", list(group)))
            except Exception:
                logger.exception("pubmed elink failed for %d accession(s)", len(group))

    pmids = list(dict.fromkeys(linked))[: max(0, max_pmids)]
    if not pmids:
        logger.info("pubmed elink: no PubMed links for %d accession(s)", len(unique))
        return ImportReport()

    report = await ingest_pmids(pmids)
    logger.info("pubmed elink import finished: %s", report.as_dict())
    return report
