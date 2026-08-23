"""ENA fetcher: Portal API metadata + Browser API residues.

The Portal API supplies verifiable metadata (tax_id, scientific name, molecule
type, description); the Browser API supplies the actual residues as FASTA.
Records missing organism identity at the source are skipped, never completed
by hand.
"""

from __future__ import annotations

from typing import Any

from app.pipeline.fetchers.base import import_with_run
from app.pipeline.logging import get_logger
from app.pipeline.models import ImportReport, ParsedOrganism, ParsedSequence
from app.services.connectors.ena import ENAConnector

logger = get_logger("biowiki.pipeline.fetchers.ena")

_FIELDS = [
    "accession",
    "sequence_version",
    "description",
    "tax_id",
    "scientific_name",
    "mol_type",
    "last_updated",
]


def _classify(mol_type: str) -> tuple[str, str | None, dict[str, str | None]]:
    """Map ENA ``mol_type`` to (seq_type, molecule, feature defaults)."""
    lowered = mol_type.lower()
    if "rna" in lowered:
        rna_class = "mrna" if "mrna" in lowered else "rrna" if "rrna" in lowered else "trna" if "trna" in lowered else "other"
        return "rna", "rna", {"rna_class": rna_class}
    if "protein" in lowered:
        return "protein", "protein", {}
    molecule_type = "mrna" if "mrna" in lowered else "genomic"
    return "dna", "dna", {"molecule_type": molecule_type}


def _strip_fasta(content: str) -> str:
    lines = [l.strip() for l in content.splitlines() if l.strip() and not l.startswith(">")]
    return "".join(lines).upper()


async def fetch_records(
    accessions: list[str],
    *,
    seq_type: str | None = None,
    connector: ENAConnector | None = None,
) -> list[ParsedSequence]:
    if not accessions:
        raise ValueError("Provide at least one ENA accession.")

    owns = connector is None
    conn = connector or ENAConnector()
    parsed: list[ParsedSequence] = []
    try:
        for accession in dict.fromkeys(a.strip() for a in accessions if a.strip()):
            page = await conn.search(
                f'accession="{accession}"', result="sequence", fields=_FIELDS, limit=1
            )
            if not page.hits:
                logger.warning("ena: no portal metadata for %s; skipped", accession)
                continue
            meta: dict[str, Any] = page.hits[0].data or {}

            tax_id_raw = str(meta.get("tax_id", "")).strip()
            scientific_name = (meta.get("scientific_name") or "").strip()
            if not tax_id_raw.isdigit() or not scientific_name:
                logger.warning("ena: %s lacks organism identity at source; skipped", accession)
                continue

            record = await conn.fetch_record(accession, fmt="fasta")
            residues = _strip_fasta(record.content)
            if not residues:
                logger.warning("ena: %s returned no residues; skipped", accession)
                continue

            mol_type = meta.get("mol_type") or ""
            inferred_type, molecule, defaults = _classify(mol_type)
            record_type = seq_type or inferred_type

            ps = ParsedSequence(
                seq_type=record_type,
                accession=accession.split(".")[0],
                name=meta.get("description") or accession,
                organism=ParsedOrganism(
                    scientific_name=scientific_name, tax_id=int(tax_id_raw)
                ),
                source_key="ena",
                source_name="EMBL-EBI ENA",
                version=str(meta.get("sequence_version") or "").strip() or None,
                description=meta.get("description"),
                molecule=molecule,
                residues=residues,
                source_url=f"https://www.ebi.ac.uk/ena/browser/view/{accession}",
                annotations={"mol_type": mol_type} if mol_type else None,
            )
            for key, value in defaults.items():
                if getattr(ps, key, None) is None:
                    setattr(ps, key, value)
            parsed.append(ps)
    finally:
        if owns:
            await conn.aclose()

    logger.info("ena fetch: %d record(s) parsed", len(parsed))
    return parsed


async def ingest(
    accessions: list[str],
    *,
    seq_type: str | None = None,
    batch_size: int = 200,
) -> ImportReport:
    records = await fetch_records(accessions, seq_type=seq_type)
    return await import_with_run(
        records,
        source_key="ena",
        kind="fetch_accessions",
        params={"accessions": accessions, "seq_type": seq_type},
        batch_size=batch_size,
    )
