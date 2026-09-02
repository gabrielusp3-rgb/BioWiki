"""Resolve remaining closeout verifier residuals without restarting 16,433 NCBI fetches.

Rewrites gitignored checkpoint JSONL under `.audit/external_verify/`.
Publication title writes require `--apply`. Never prints secrets.
"""

from __future__ import annotations

import argparse
import asyncio
import html
import json
import re
import unicodedata
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import func, select

from app.database.session import get_sessionmaker
from app.models.organism import Organism
from app.models.publication import Publication
from app.models.sequence import Sequence
from app.pipeline.fetchers.base import chunked
from app.pipeline.paleogenomics.semantics import normalize_doi
from app.services.connectors.datasets import NCBIDatasetsConnector
from app.services.connectors.ncbi import NCBIConnector
from app.services.connectors.pdb import PDBConnector
from app.services.integrity_checks import sql_integrity_checks
from verify_external_catalogue import (
    STATE_DIR,
    _now,
    _verify_pdb_polymer,
    write_summary,
)

PUBMED_XML_CHUNK = 50


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    tmp.replace(path)


class _SeqProxy:
    __slots__ = ("id", "accession", "version", "seq_type", "source_key", "checksum")

    def __init__(self, rec: dict[str, Any], checksum: str):
        self.id = rec["id"]
        self.accession = rec["accession"]
        self.version = rec.get("version")
        self.seq_type = type("T", (), {"value": rec.get("type") or "protein"})()
        self.source_key = rec.get("source") or "pdb"
        self.checksum = checksum


async def resolve_pdb() -> dict[str, int]:
    path = STATE_DIR / "sequences.jsonl"
    rows = _load_jsonl(path)
    pending = [
        r
        for r in rows
        if r.get("status") == "TEMPORARILY_UNVERIFIED"
        and (r.get("source") or "").lower() in {"pdb", "rcsb"}
    ]
    print(f"pdb residuals {len(pending)}", flush=True)
    if not pending:
        return Counter()
    ids = [UUID(r["id"]) for r in pending]
    async with get_sessionmaker()() as session:
        stored_rows = (
            await session.execute(
                select(Sequence.id, Sequence.residues, Sequence.checksum, Sequence.length).where(
                    Sequence.id.in_(ids)
                )
            )
        ).all()
    by_id = {str(row[0]): row for row in stored_rows}
    counts: Counter[str] = Counter()
    async with PDBConnector() as pdb:
        for rec in pending:
            row = by_id.get(rec["id"])
            residues = row[1] if row else ""
            checksum = row[2] if row else ""
            proxy = _SeqProxy(rec, checksum or "")
            updated = await _verify_pdb_polymer(pdb, proxy, residues or "")
            rec.clear()
            rec.update(updated)
            counts[updated["status"]] += 1
            print(f"  {updated['accession']} {updated['status']}", flush=True)
    _write_jsonl(path, rows)
    return dict(counts)


def _query_keys(node: dict[str, Any]) -> list[str]:
    query = node.get("query")
    if isinstance(query, list):
        return [str(item) for item in query if item is not None]
    if query is not None:
        return [str(query)]
    tax = node.get("taxonomy") if isinstance(node.get("taxonomy"), dict) else {}
    tax_id = tax.get("tax_id") or tax.get("taxId")
    return [str(tax_id)] if tax_id is not None else []


def _taxonomy_node(payload: dict[str, Any]) -> dict[str, Any]:
    if "taxonomy" in payload and isinstance(payload["taxonomy"], dict):
        return payload["taxonomy"]
    return payload


def _taxonomy_errors(node: dict[str, Any] | None) -> str | None:
    if not node:
        return None
    errors = node.get("errors")
    if isinstance(errors, list) and errors:
        first = errors[0]
        if isinstance(first, dict):
            return str(first.get("reason") or first)
        return str(first)
    if isinstance(errors, str):
        return errors
    return None


def _index_taxonomy_nodes(nodes: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_key: dict[str, dict[str, Any]] = {}
    for node in nodes:
        for key in _query_keys(node):
            by_key[key] = node
            by_key[key.lower()] = node
        tax = _taxonomy_node(node)
        tax_id = tax.get("tax_id") or tax.get("taxId")
        if tax_id is not None:
            by_key[str(tax_id)] = node
        name = _current_name(tax)
        if name:
            by_key[_norm_name(name)] = node
    return by_key


def _current_name(tax: dict[str, Any]) -> str | None:
    for key in (
        "current_scientific_name",
        "currentScientificName",
        "organism_name",
        "organismName",
        "scientific_name",
        "scientificName",
    ):
        value = tax.get(key)
        if isinstance(value, dict):
            value = value.get("name") or value.get("value")
        if value:
            return str(value)
    return None


def _norm_name(value: str | None) -> str:
    return re.sub(r"\s+", " ", (value or "").strip().lower())


def _collect_synonyms(tax: dict[str, Any]) -> list[str]:
    names: list[str] = []
    buckets = [
        tax.get("synonyms"),
        tax.get("other_scientific_names"),
        tax.get("otherScientificNames"),
        tax.get("homotypic_synonyms"),
        tax.get("homotypicSynonyms"),
        tax.get("heterotypic_synonyms"),
        tax.get("heterotypicSynonyms"),
        tax.get("other_synonyms"),
        tax.get("otherSynonyms"),
    ]
    csn = tax.get("current_scientific_name") or tax.get("currentScientificName")
    if isinstance(csn, dict):
        for key in ("curator_synonym", "curatorSynonym", "basionym"):
            buckets.append(csn.get(key))
        for key in ("homotypic_synonyms", "homotypicSynonyms", "heterotypic_synonyms", "heterotypicSynonyms", "other_synonyms", "otherSynonyms"):
            buckets.append(csn.get(key))
    for bucket in buckets:
        if isinstance(bucket, str):
            names.append(bucket)
        elif isinstance(bucket, dict):
            names.append(str(bucket.get("name") or bucket.get("value") or ""))
        elif isinstance(bucket, list):
            for item in bucket:
                if isinstance(item, str):
                    names.append(item)
                elif isinstance(item, dict):
                    names.append(str(item.get("name") or item.get("value") or ""))
    return [n for n in names if n]


def _classify_name(stored: str, current: str | None, tax: dict[str, Any]) -> str:
    if tax.get("status") == "merged" or tax.get("merged_from") or tax.get("mergedFrom"):
        return "MERGED_TAXID"
    if not current:
        return "TEMPORARILY_UNVERIFIED"
    a = _norm_name(stored)
    b = _norm_name(current)
    if a == b:
        return "TAXONOMY_EXACT"
    if a in {_norm_name(n) for n in _collect_synonyms(tax)}:
        return "SYNONYM_ACCEPTABLE"
    return "NAME_MISMATCH"


async def resolve_taxonomy() -> dict[str, int]:
    path = STATE_DIR / "organisms.jsonl"
    rows = _load_jsonl(path)
    pending = [r for r in rows if r.get("status") == "TEMPORARILY_UNVERIFIED"]
    print(f"taxonomy residuals {len(pending)}", flush=True)
    if not pending:
        return {}
    counts: Counter[str] = Counter()
    async with NCBIDatasetsConnector() as datasets:
        for chunk in chunked(pending, 20):
            ids = [r["tax_id"] for r in chunk]
            print(f"datasets taxonomy {ids[0]}… ({len(chunk)})", flush=True)
            try:
                nodes = await datasets.taxonomy_reports(ids)
            except Exception as exc:
                for rec in chunk:
                    rec["status"] = "TEMPORARILY_UNVERIFIED"
                    rec["detail"] = type(exc).__name__
                    rec["provider"] = "ncbi_datasets"
                    rec["checked_at"] = _now()
                    counts["TEMPORARILY_UNVERIFIED"] += 1
                continue
            by_tax = _index_taxonomy_nodes(nodes)
            try:
                name_nodes = await datasets.taxonomy_name_reports(ids)
            except Exception:
                name_nodes = []
            by_tax.update(_index_taxonomy_nodes(name_nodes))
            for rec in chunk:
                tax_id = str(rec.get("tax_id"))
                node = by_tax.get(tax_id)
                tax = _taxonomy_node(node) if node else {}
                current = _current_name(tax)
                if current:
                    status = _classify_name(rec.get("scientific_name") or "", current, tax)
                    rec["status"] = status
                    rec["remote_name"] = current
                    rec["rank"] = tax.get("rank")
                    rec["remote_tax_id"] = str(tax.get("tax_id") or tax.get("taxId") or tax_id)
                    rec["provider"] = "ncbi_datasets_name_report"
                    rec["checked_at"] = _now()
                    rec.pop("detail", None)
                    counts[status] += 1
                    continue
                rec["status"] = "TEMPORARILY_UNVERIFIED"
                rec["detail"] = _taxonomy_errors(node) or "unknown taxid at NCBI Datasets"
                rec["provider"] = "ncbi_datasets"
                rec["checked_at"] = _now()
                counts["TEMPORARILY_UNVERIFIED"] += 1
        extra = await _resolve_taxonomy_by_name(
            datasets, [r for r in rows if r.get("status") == "TEMPORARILY_UNVERIFIED"]
        )
        for status, n in extra.items():
            counts[status] += n
            if status != "TEMPORARILY_UNVERIFIED":
                counts["TEMPORARILY_UNVERIFIED"] = max(
                    0, counts["TEMPORARILY_UNVERIFIED"] - n
                )
    _write_jsonl(path, rows)
    return dict(counts)


async def _resolve_taxonomy_by_name(
    datasets: NCBIDatasetsConnector, pending: list[dict[str, Any]]
) -> dict[str, int]:
    """Lookup unresolved TaxIDs by scientific name. Does not rewrite stored tax_id."""
    counts: Counter[str] = Counter()
    if not pending:
        return {}
    async with NCBIConnector() as ncbi:
        for rec in pending:
            name = (rec.get("scientific_name") or "").strip()
            if not name:
                rec["detail"] = "ncbi_datasets_unknown_taxid_and_empty_name"
                continue
            node = None
            try:
                nodes = await datasets.taxonomy_name_reports([name])
                indexed = _index_taxonomy_nodes(nodes)
                node = indexed.get(_norm_name(name)) or next(iter(indexed.values()), None)
            except Exception as exc:
                rec["detail"] = f"datasets_name_lookup:{type(exc).__name__}"
            tax = _taxonomy_node(node) if node else {}
            current = _current_name(tax)
            remote_tax = str(tax.get("tax_id") or tax.get("taxId") or "")
            if current and remote_tax and remote_tax != str(rec.get("tax_id")):
                    rec["detail"] = (
                        f"stored_taxid_unknown_at_ncbi; name_resolves_to_taxid={remote_tax}"
                    )
                    rec["status"] = "TEMPORARILY_UNVERIFIED"
                    rec["remote_name"] = current
                    rec["remote_tax_id"] = remote_tax
                    rec["rank"] = tax.get("rank")
                    rec["provider"] = "ncbi_datasets_name_report"
                    rec["checked_at"] = _now()
                    continue
            try:
                page = await ncbi.esearch("taxonomy", name, retmax=5)
            except Exception as exc:
                rec["detail"] = (
                    rec.get("detail") or _taxonomy_errors(node) or "unknown taxid at NCBI Datasets"
                ) + f"; esearch:{type(exc).__name__}"
                rec["checked_at"] = _now()
                continue
            if page.total == 0 or not page.hits:
                rec["detail"] = (
                    "ncbi_datasets_and_taxonomy_esearch_unknown_taxid_and_name"
                )
                rec["provider"] = "ncbi_datasets+taxonomy_esearch"
                rec["checked_at"] = _now()
                continue
            rec["detail"] = (
                "stored_taxid_unknown_at_ncbi; name_esearch_hits="
                + ",".join(h.identifier for h in page.hits[:5])
            )
            rec["provider"] = "ncbi_taxonomy_esearch"
            rec["checked_at"] = _now()
            rec["status"] = "TEMPORARILY_UNVERIFIED"
    return dict(counts)


def _strip_tags(value: str) -> str:
    return re.sub(r"<[^>]+>", " ", value)


def _format_norm(value: str | None) -> str:
    if not value:
        return ""
    text = html.unescape(html.unescape(value))
    text = _strip_tags(text)
    text = unicodedata.normalize("NFKC", text)
    table = str.maketrans(
        {
            "\u2018": "'",
            "\u2019": "'",
            "\u201c": '"',
            "\u201d": '"',
            "\u2013": "-",
            "\u2014": "-",
            "\u00a0": " ",
        }
    )
    text = text.translate(table)
    text = re.sub(r"\s+", " ", text).strip().lower()
    text = text.strip(" .;:")
    if text.startswith("[") and text.endswith("]"):
        text = text[1:-1].strip()
    return text


def _classify_titles(local: str, remote: str) -> str:
    a = _format_norm(local)
    b = _format_norm(remote)
    if not b:
        return "TEMPORARILY_UNVERIFIED"
    if a == b:
        return "FORMAT_EQUIVALENT"
    if a and b.startswith(a) and len(b) - len(a) >= 8:
        return "LOCAL_METADATA_TRUNCATED"
    if b and a.startswith(b) and len(a) - len(b) >= 8:
        return "REMOTE_METADATA_NEWER"
    return "REMOTE_METADATA_NEWER"


def _parse_pubmed_xml(raw: str) -> dict[int, dict[str, Any]]:
    out: dict[int, dict[str, Any]] = {}
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        return out
    for article in list(root.iter("PubmedArticle")) + list(root.iter("PubmedBookArticle")):
        pmid_el = article.find(".//PMID")
        if pmid_el is None or not (pmid_el.text or "").strip():
            continue
        pmid = int(pmid_el.text.strip())
        title_el = article.find(".//ArticleTitle")
        if title_el is None:
            title_el = article.find(".//BookTitle")
        title = "".join(title_el.itertext()).strip() if title_el is not None else ""
        journal_el = article.find(".//Journal/Title")
        year_el = article.find(".//JournalIssue/PubDate/Year")
        doi = None
        for aid in article.findall(".//ArticleId"):
            if (aid.get("IdType") or "").lower() == "doi" and aid.text:
                doi = aid.text.strip()
                break
        out[pmid] = {
            "title": title,
            "journal": (journal_el.text or "").strip() if journal_el is not None else None,
            "year": int(year_el.text) if year_el is not None and (year_el.text or "").isdigit() else None,
            "doi": doi,
        }
    return out


async def resolve_pubmed(*, apply: bool) -> dict[str, int]:
    path = STATE_DIR / "publications.jsonl"
    rows = _load_jsonl(path)
    pending = [
        r
        for r in rows
        if r.get("pubmed_id")
        and r.get("status") in {"METADATA_MISMATCH", "TEMPORARILY_UNVERIFIED"}
    ]
    print(f"pubmed residuals {len(pending)}", flush=True)
    counts: Counter[str] = Counter()
    updates: list[tuple[UUID, str]] = []
    if pending:
        async with NCBIConnector() as ncbi:
            for chunk in chunked(pending, PUBMED_XML_CHUNK):
                ids = [str(r["pubmed_id"]) for r in chunk]
                print(f"pubmed efetch xml {len(ids)} (first {ids[0]})", flush=True)
                try:
                    raw = await ncbi.efetch("pubmed", ids, rettype="xml", retmode="xml")
                    remote_map = _parse_pubmed_xml(raw)
                except Exception as exc:
                    for rec in chunk:
                        rec["status"] = "TEMPORARILY_UNVERIFIED"
                        rec["detail"] = type(exc).__name__
                        rec["checked_at"] = _now()
                        counts["TEMPORARILY_UNVERIFIED"] += 1
                    continue
                pub_ids = [UUID(r["id"]) for r in chunk]
                async with get_sessionmaker()() as session:
                    pubs = {
                        str(p.id): p
                        for p in (
                            await session.execute(select(Publication).where(Publication.id.in_(pub_ids)))
                        ).scalars()
                    }
                for rec in chunk:
                    pub = pubs.get(rec["id"])
                    remote = remote_map.get(int(rec["pubmed_id"]))
                    if pub is None or not remote or not (remote.get("title") or "").strip():
                        rec["status"] = "TEMPORARILY_UNVERIFIED"
                        rec["detail"] = "missing local row or xml article"
                        rec["checked_at"] = _now()
                        counts["TEMPORARILY_UNVERIFIED"] += 1
                        continue
                    status = _classify_titles(pub.title, remote["title"])
                    rec["status"] = status
                    rec["detail"] = None
                    rec["remote_title"] = remote["title"]
                    rec["provider"] = "pubmed_efetch_xml"
                    rec["checked_at"] = _now()
                    counts[status] += 1
    seen: set[str] = set()
    for rec in rows:
        if rec.get("status") not in {"LOCAL_METADATA_TRUNCATED", "REMOTE_METADATA_NEWER"}:
            continue
        title = (rec.get("remote_title") or "").strip()
        rec_id = rec.get("id")
        if not title or not rec_id or rec_id in seen:
            continue
        seen.add(rec_id)
        updates.append((UUID(rec_id), title))
    _write_jsonl(path, rows)
    if apply and updates:
        print(f"applying {len(updates)} publication title updates", flush=True)
        async with get_sessionmaker()() as session:
            async with session.begin():
                for pub_id, title in updates:
                    pub = await session.get(Publication, pub_id)
                    if pub is None:
                        continue
                    pub.title = title
            await session.commit()
        by_uuid = {str(pub_id): True for pub_id, _title in updates}
        for rec in rows:
            if rec.get("id") in by_uuid and rec.get("status") in {
                "LOCAL_METADATA_TRUNCATED",
                "REMOTE_METADATA_NEWER",
            }:
                rec["status"] = "METADATA_CORRECTED"
                rec["checked_at"] = _now()
        counts["METADATA_CORRECTED"] = len(updates)
        _write_jsonl(path, rows)
    elif updates:
        print(f"would update {len(updates)} titles (pass --apply)", flush=True)
        counts["PENDING_TITLE_UPDATES"] = len(updates)
    return dict(counts)


async def duplicate_audit() -> dict[str, Any]:
    async with get_sessionmaker()() as session:
        checks = await sql_integrity_checks(session)
        wanted = {
            "publications:unique_pmid",
            "publications:unique_normalized_doi",
            "references:sequence_id_exists",
            "references:publication_id_exists",
        }
        picked = [c for c in checks if c.name in wanted]
        pmid_count = int(
            (
                await session.execute(
                    select(func.count(func.distinct(Publication.pubmed_id))).where(
                        Publication.pubmed_id.is_not(None)
                    )
                )
            ).scalar_one()
        )
        pub_count = int((await session.execute(select(func.count()).select_from(Publication))).scalar_one())
    return {
        "publications": pub_count,
        "unique_pmids": pmid_count,
        "checks": [
            {"name": c.name, "ok": c.ok, "expected": c.expected, "actual": c.actual}
            for c in picked
        ],
    }


async def async_main(apply: bool) -> int:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    pdb = await resolve_pdb()
    tax = await resolve_taxonomy()
    pubs = await resolve_pubmed(apply=apply)
    summary = write_summary()
    audit = await duplicate_audit()
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pdb": pdb,
        "taxonomy": tax,
        "pubmed": pubs,
        "checkpoint": summary,
        "integrity": audit,
    }
    (STATE_DIR / "residuals_report.json").write_text(
        json.dumps(report, indent=2, default=str), encoding="utf-8"
    )
    print(json.dumps(report, indent=2, default=str))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write Publication.title updates for truncated/newer PubMed XML titles.",
    )
    args = parser.parse_args()
    return asyncio.run(async_main(args.apply))


if __name__ == "__main__":
    raise SystemExit(main())
