"""Discover catalogue-appropriate paleogenomic accessions. No SRA-read inflation."""

from __future__ import annotations

from typing import Any

from app.pipeline.paleogenomics.catalogue import PaleogenomicSpecies
from app.pipeline.paleogenomics.semantics import (
    sequence_length_allowed_for_catalogue,
    sra_run_is_not_a_sequence_accession,
)
from app.services.connectors.ncbi import NCBIConnector

NUCCORE_TERM = (
    "txid{tax_id}[Organism:noexp] NOT wgs[filter] NOT tsa[filter] NOT sra[filter]"
)
PROTEIN_TERM = "txid{tax_id}[Organism:noexp]"


def _summary_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    result = payload.get("result") or {}
    uids = result.get("uids") or []
    rows: list[dict[str, Any]] = []
    for uid in uids:
        rec = result.get(str(uid)) or result.get(uid)
        if not isinstance(rec, dict):
            continue
        rows.append(rec)
    return rows


def _int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def score_candidate(title: str, length: int | None) -> int:
    text = title.lower()
    score = 0
    if "complete" in text and ("mitochond" in text or "mitogenome" in text or "mtdna" in text):
        score += 100
    if "mitochond" in text:
        score += 20
    if any(token in text for token in ("cytochrome", "cytb", "cox1", "coi", "d-loop")):
        score += 15
    if "genome" in text and length and 14000 <= length <= 20000:
        score += 25
    if "shotgun" in text or "wgs" in text:
        score -= 50
    if length and length > 80000:
        score -= 20
    return score


def title_key(title: str) -> str:
    return " ".join(title.lower().split())[:96]


async def discover_accessions(
    species: PaleogenomicSpecies,
    *,
    db: str = "nuccore",
    search_limit: int,
    keep: int,
    molecule: str = "dna",
) -> dict[str, Any]:
    term = (NUCCORE_TERM if db == "nuccore" else PROTEIN_TERM).format(tax_id=species.tax_id)
    rejected: list[dict[str, str]] = []
    candidates: list[dict[str, Any]] = []
    async with NCBIConnector() as conn:
        page = await conn.esearch(db, term, retmax=max(1, min(search_limit, 400)))
        ids = [hit.identifier for hit in page.hits if hit.identifier]
        total_hits = page.total
        for start in range(0, len(ids), 200):
            chunk = ids[start : start + 200]
            payload = await conn.esummary(db, chunk)
            for rec in _summary_rows(payload):
                accession = str(rec.get("caption") or rec.get("accessionversion") or "").split(".")[0]
                title = str(rec.get("title") or "")
                length = _int(rec.get("slen"))
                tax_id = _int(rec.get("taxid"))
                extra = str(rec.get("extra") or "")
                if not accession:
                    rejected.append({"reason": "missing_accession", "title": title[:80]})
                    continue
                if sra_run_is_not_a_sequence_accession(accession) or accession.upper().startswith(("SRS", "SRX", "ERX")):
                    rejected.append({"reason": "sra_or_run", "accession": accession})
                    continue
                if tax_id is not None and tax_id != species.tax_id:
                    rejected.append(
                        {
                            "reason": "tax_id_mismatch",
                            "accession": accession,
                            "tax_id": str(tax_id),
                        }
                    )
                    continue
                if not sequence_length_allowed_for_catalogue(length, molecule=molecule):
                    rejected.append(
                        {
                            "reason": "length_not_catalogue",
                            "accession": accession,
                            "length": str(length or ""),
                        }
                    )
                    continue
                if "shotgun" in title.lower() and (length or 0) > 50000:
                    rejected.append({"reason": "wgs_like", "accession": accession})
                    continue
                candidates.append(
                    {
                        "accession": accession,
                        "version": extra.split(".")[-1] if "." in extra else None,
                        "title": title,
                        "length": length,
                        "tax_id": tax_id or species.tax_id,
                        "score": score_candidate(title, length),
                    }
                )
    candidates.sort(key=lambda row: (-int(row["score"]), int(row["length"] or 0), row["accession"]))
    seen_titles: set[str] = set()
    diverse: list[dict[str, Any]] = []
    for row in candidates:
        key = title_key(str(row["title"]))
        if key in seen_titles and len(diverse) >= max(8, keep // 4):
            continue
        seen_titles.add(key)
        diverse.append(row)
        if len(diverse) >= keep:
            break
    return {
        "term": term,
        "db": db,
        "total_hits": total_hits,
        "summaries_kept": len(diverse),
        "summaries_rejected": len(rejected),
        "rejected_sample": rejected[:25],
        "accessions": [row["accession"] for row in diverse],
        "candidates": diverse,
    }
