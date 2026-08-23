"""Rfam fetcher: RNA family members ingested with full NCBI provenance.

Rfam seed alignments reference real INSDC accessions (``ACC.v/start-end``).
Rather than importing gapped alignment slices with unknown organisms, this
fetcher resolves the member accessions and ingests the underlying records from
NCBI (organism, taxonomy, references included), tagging each with the Rfam
family as a cross-reference.
"""

from __future__ import annotations

import re

from app.pipeline.fetchers import ncbi as ncbi_fetcher
from app.pipeline.fetchers.base import import_with_run
from app.pipeline.logging import get_logger
from app.pipeline.models import ImportReport, ParsedXref
from app.services.connectors.errors import ConnectorError
from app.services.connectors.rfam import RfamConnector
from app.services.connectors.rfam.client import RFAM_API_DOC

logger = get_logger("biowiki.pipeline.fetchers.rfam")

_MEMBER_RE = re.compile(r"^>(\S+?)/(\d+)-(\d+)", re.MULTILINE)

# Rfam curation "type" string → our rna_class enum value.
_TYPE_MAP = [
    ("rrna", "rrna"),
    ("trna", "trna"),
    ("mirna", "mirna"),
    ("snrna", "snrna"),
    ("lncrna", "lncrna"),
]


def _rna_class_from_family(family_type: str) -> str:
    lowered = family_type.lower()
    for needle, value in _TYPE_MAP:
        if needle in lowered:
            return value
    return "other"


async def ingest_family(
    rfam_acc: str,
    *,
    limit: int = 25,
    batch_size: int = 200,
) -> ImportReport:
    family_id = rfam_acc
    family_type = ""
    rest_ok = True
    try:
        async with RfamConnector() as conn:
            try:
                payload = await conn.family(rfam_acc)
                family = payload.get("rfam") if isinstance(payload, dict) else None
                family = family if isinstance(family, dict) else {}
                family_id = family.get("id") or rfam_acc
                curation = family.get("curation") or {}
                family_type = str(curation.get("type") or "")
            except ConnectorError as exc:
                rest_ok = False
                logger.warning(
                    "rfam REST metadata unavailable for %s (%s); "
                    "continuing with official FTP FASTA if present",
                    rfam_acc,
                    exc,
                )
            try:
                alignment = await conn.alignment_fasta(rfam_acc, use_rest=rest_ok)
            except ConnectorError as exc:
                message = (
                    f"rfam {rfam_acc}: source unavailable ({exc}). "
                    f"Documented API: {RFAM_API_DOC}. No records invented."
                )
                logger.warning(message)
                return ImportReport(failed=1, errors=[message])
    except ConnectorError as exc:
        message = (
            f"rfam {rfam_acc}: source unavailable ({exc}). "
            f"Documented API: {RFAM_API_DOC}. No records invented."
        )
        logger.warning(message)
        return ImportReport(failed=1, errors=[message])

    member_accessions = list(
        dict.fromkeys(match.group(1) for match in _MEMBER_RE.finditer(alignment.content))
    )[: max(1, limit)]
    if not member_accessions:
        logger.warning("rfam: family %s has no resolvable seed members", rfam_acc)
        return ImportReport()

    rna_class = _rna_class_from_family(family_type)
    records = await ncbi_fetcher.fetch_records(member_accessions, db="nuccore", seq_type="rna")

    for ps in records:
        if ps.rna_class is None:
            ps.rna_class = rna_class
        ps.cross_references.append(
            ParsedXref(
                db_name="rfam",
                external_id=rfam_acc,
                url=f"https://rfam.org/family/{rfam_acc}",
            )
        )
        if ps.annotations is None:
            ps.annotations = {}
        ps.annotations["rfam_family"] = {"accession": rfam_acc, "id": family_id}

    return await import_with_run(
        records,
        source_key="rfam",
        kind="fetch_family",
        params={"rfam_acc": rfam_acc, "limit": limit, "members": member_accessions},
        batch_size=batch_size,
    )
