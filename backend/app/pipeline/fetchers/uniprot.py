"""UniProt fetcher: UniProtKB entry JSON → protein records.

Every field is copied from the real entry: sequence, gene, organism lineage,
review status (Swiss-Prot vs TrEMBL), function annotation, PDB links and the
entry's own literature citations (with PubMed IDs / DOIs).
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from app.pipeline.fetchers.base import chunked, import_with_run
from app.pipeline.logging import get_logger
from app.pipeline.models import (
    ImportReport,
    ParsedOrganism,
    ParsedPublication,
    ParsedSequence,
    ParsedXref,
)
from app.services.connectors.uniprot import UniProtConnector

logger = get_logger("biowiki.pipeline.fetchers.uniprot")

_YEAR_RE = re.compile(r"\b(1[89]\d{2}|20\d{2})\b")


def _entry_to_parsed(entry: dict[str, Any]) -> ParsedSequence | None:
    accession = entry.get("primaryAccession")
    sequence = entry.get("sequence") or {}
    residues = sequence.get("value")
    if not accession or not residues:
        return None

    organism_data = entry.get("organism") or {}
    tax_id = organism_data.get("taxonId")
    scientific_name = organism_data.get("scientificName")
    if not tax_id or not scientific_name:
        return None
    from app.pipeline.validation import normalize_lineage

    organism = ParsedOrganism(
        scientific_name=scientific_name,
        tax_id=int(tax_id),
        common_name=organism_data.get("commonName"),
        lineage=normalize_lineage(organism_data.get("lineage") or []),
    )

    description = entry.get("proteinDescription") or {}
    name = (
        ((description.get("recommendedName") or {}).get("fullName") or {}).get("value")
        or next(
            (
                ((sub.get("fullName") or {}).get("value"))
                for sub in description.get("submissionNames") or []
                if (sub.get("fullName") or {}).get("value")
            ),
            None,
        )
        or entry.get("uniProtkbId")
        or accession
    )

    gene_name = None
    genes = entry.get("genes") or []
    if genes and isinstance(genes[0], dict):
        gene_name = ((genes[0].get("geneName") or {}).get("value"))

    function = None
    for comment in entry.get("comments") or []:
        if comment.get("commentType") == "FUNCTION":
            texts = comment.get("texts") or []
            if texts:
                function = texts[0].get("value")
            break

    pdb_ids: list[str] = []
    xrefs: list[ParsedXref] = []
    for xref in entry.get("uniProtKBCrossReferences") or []:
        database = xref.get("database")
        external_id = xref.get("id")
        if not database or not external_id:
            continue
        if database == "PDB":
            pdb_ids.append(external_id)
            xrefs.append(
                ParsedXref(
                    db_name="pdb",
                    external_id=external_id,
                    url=f"https://www.rcsb.org/structure/{external_id}",
                )
            )

    domains = [
        feature.get("description")
        for feature in entry.get("features") or []
        if feature.get("type") == "Domain" and feature.get("description")
    ]

    publications: list[ParsedPublication] = []
    for order, reference in enumerate(entry.get("references") or [], start=1):
        citation = reference.get("citation") or {}
        title = citation.get("title")
        pubmed_id = doi = None
        for cross_ref in citation.get("citationCrossReferences") or []:
            if cross_ref.get("database") == "PubMed" and str(cross_ref.get("id", "")).isdigit():
                pubmed_id = int(cross_ref["id"])
            elif cross_ref.get("database") == "DOI":
                doi = cross_ref.get("id")
        if not title and not pubmed_id:
            continue
        year = None
        year_match = _YEAR_RE.search(str(citation.get("publicationDate", "")))
        if year_match:
            year = int(year_match.group(1))
        publications.append(
            ParsedPublication(
                title=title,
                pubmed_id=pubmed_id,
                doi=doi,
                authors=list(citation.get("authors") or []),
                journal=citation.get("journal"),
                year=year,
                volume=citation.get("volume"),
                pages=(
                    f"{citation.get('firstPage')}-{citation.get('lastPage')}"
                    if citation.get("firstPage") and citation.get("lastPage")
                    else None
                ),
                url=f"https://pubmed.ncbi.nlm.nih.gov/{pubmed_id}/" if pubmed_id else None,
                reference_order=order,
            )
        )

    audit = entry.get("entryAudit") or {}
    source_updated_at = None
    for key in ("lastSequenceUpdateDate", "lastAnnotationUpdateDate"):
        raw = audit.get(key)
        if raw:
            try:
                source_updated_at = datetime.fromisoformat(raw).replace(tzinfo=timezone.utc)
                break
            except ValueError:
                continue

    entry_type = str(entry.get("entryType", ""))
    sequence_version = audit.get("sequenceVersion")

    return ParsedSequence(
        seq_type="protein",
        accession=accession,
        name=name,
        organism=organism,
        source_key="uniprot",
        source_name="UniProt",
        version=str(sequence_version) if sequence_version else None,
        description=function or name,
        molecule="protein",
        residues=residues,
        length=sequence.get("length"),
        source_updated_at=source_updated_at,
        gene=gene_name,
        gene_name=gene_name,
        reviewed="reviewed" in entry_type.lower() and "unreviewed" not in entry_type.lower(),
        molecular_weight=sequence.get("molWeight"),
        function=function,
        pdb_ids=pdb_ids,
        domains=[d for d in domains if d],
        source_url=f"https://www.uniprot.org/uniprotkb/{accession}/entry",
        cross_references=xrefs,
        publications=publications,
    )


async def fetch_records(
    accessions: list[str] | None = None,
    *,
    query: str | None = None,
    limit: int = 100,
    connector: UniProtConnector | None = None,
) -> list[ParsedSequence]:
    if not accessions and not query:
        raise ValueError("Provide accessions or a query.")

    owns = connector is None
    conn = connector or UniProtConnector()
    parsed: list[ParsedSequence] = []
    try:
        ids = list(dict.fromkeys(accessions or []))
        if query:
            fetched = 0
            cursor = None
            while fetched < limit:
                page = await conn.search(query, size=min(50, limit - fetched), cursor=cursor)
                if not page.hits:
                    break
                ids.extend(hit.identifier for hit in page.hits if hit.identifier)
                fetched += len(page.hits)
                cursor = page.next_cursor
                if cursor is None:
                    break
            ids = list(dict.fromkeys(ids))

        seen: set[str] = set()
        for group in chunked(ids, 50):
            try:
                payload = await conn.get_accessions(list(group))
                entries = payload.get("results") if isinstance(payload, dict) else None
                if not isinstance(entries, list):
                    raise ValueError("UniProt accessions payload missing results")
                for entry in entries:
                    record = _entry_to_parsed(entry)
                    if record is None:
                        continue
                    if record.accession in seen:
                        continue
                    seen.add(record.accession)
                    parsed.append(record)
            except Exception:
                logger.exception(
                    "uniprot batch lookup failed (%d ids); retrying one-by-one",
                    len(group),
                )
                for accession in group:
                    if accession in seen:
                        continue
                    try:
                        entry = await conn.get_entry_json(accession)
                        record = _entry_to_parsed(entry)
                        if record is None:
                            logger.warning(
                                "uniprot entry %s lacks sequence/organism; skipped",
                                accession,
                            )
                            continue
                        seen.add(record.accession)
                        parsed.append(record)
                    except Exception:
                        logger.exception("uniprot entry skipped %s", accession)
    finally:
        if owns:
            await conn.aclose()

    logger.info("uniprot fetch: %d record(s) parsed", len(parsed))
    return parsed


async def ingest(
    accessions: list[str] | None = None,
    *,
    query: str | None = None,
    limit: int = 100,
    batch_size: int = 200,
) -> ImportReport:
    records = await fetch_records(accessions, query=query, limit=limit)
    return await import_with_run(
        records,
        source_key="uniprot",
        kind="fetch_accessions" if accessions else "fetch_search",
        params={"accessions": accessions, "query": query, "limit": limit},
        batch_size=batch_size,
    )
