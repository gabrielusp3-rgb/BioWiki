"""Ensembl fetcher: REST lookup + sequence + taxonomy resolution.

The organism's NCBI tax ID is resolved through Ensembl's own taxonomy endpoint
(``/taxonomy/name/{species}``) — a real cross-database identifier, never
guessed. Records whose species cannot be resolved are skipped.
"""

from __future__ import annotations

from typing import Any

from app.pipeline.fetchers.base import import_with_run
from app.pipeline.logging import get_logger
from app.pipeline.models import ImportReport, ParsedOrganism, ParsedSequence
from app.services.connectors.ensembl import EnsemblConnector

logger = get_logger("biowiki.pipeline.fetchers.ensembl")

# Ensembl sequence kind → (seq_type, molecule, feature defaults)
_KIND_MAP: dict[str, tuple[str, str, dict[str, Any]]] = {
    "genomic": ("dna", "dna", {"molecule_type": "genomic"}),
    "cds": ("dna", "dna", {"molecule_type": "cds"}),
    "cdna": ("dna", "dna", {"molecule_type": "mrna"}),
    "protein": ("protein", "protein", {"reviewed": False}),
}


def _strip_fasta(content: str) -> str:
    lines = [l.strip() for l in content.splitlines() if l.strip() and not l.startswith(">")]
    return "".join(lines).upper()


async def _resolve_organism(
    conn: EnsemblConnector, species: str, cache: dict[str, ParsedOrganism | None]
) -> ParsedOrganism | None:
    if species in cache:
        return cache[species]
    organism: ParsedOrganism | None = None
    try:
        nodes = await conn.get_json(f"taxonomy/name/{species}")
    except Exception:  # noqa: BLE001 — treat unresolvable species as skippable
        nodes = []
    if isinstance(nodes, list):
        for node in nodes:
            if not isinstance(node, dict):
                continue
            tax_id = node.get("id")
            name = node.get("scientific_name") or node.get("name")
            if tax_id and str(tax_id).isdigit() and name:
                organism = ParsedOrganism(scientific_name=name, tax_id=int(tax_id))
                break
    cache[species] = organism
    return organism


async def fetch_records(
    stable_ids: list[str],
    *,
    kind: str = "genomic",
    connector: EnsemblConnector | None = None,
) -> list[ParsedSequence]:
    if kind not in _KIND_MAP:
        raise ValueError(f"kind must be one of {sorted(_KIND_MAP)}")
    if not stable_ids:
        raise ValueError("Provide at least one Ensembl stable ID.")

    seq_type, molecule, defaults = _KIND_MAP[kind]
    owns = connector is None
    conn = connector or EnsemblConnector()
    organism_cache: dict[str, ParsedOrganism | None] = {}
    parsed: list[ParsedSequence] = []
    try:
        for stable_id in dict.fromkeys(s.strip() for s in stable_ids if s.strip()):
            info = await conn.lookup_id(stable_id)
            species = info.get("species")
            if not species:
                logger.warning("ensembl: %s has no species in lookup; skipped", stable_id)
                continue
            organism = await _resolve_organism(conn, species, organism_cache)
            if organism is None:
                logger.warning("ensembl: cannot resolve tax id for %s; skipped", species)
                continue

            record = await conn.sequence_id(stable_id, seq_type=kind)
            residues = _strip_fasta(record.content)
            if not residues:
                logger.warning("ensembl: %s returned no residues; skipped", stable_id)
                continue

            display_name = info.get("display_name")
            version = info.get("version")
            ps = ParsedSequence(
                seq_type=seq_type,
                accession=stable_id,
                name=info.get("description") or display_name or stable_id,
                organism=organism,
                source_key="ensembl",
                source_name="Ensembl",
                version=str(version) if version is not None else None,
                description=info.get("description"),
                molecule=molecule,
                residues=residues,
                gene_name=display_name if info.get("object_type") == "Gene" else None,
                chromosome=str(info.get("seq_region_name") or "") or None,
                source_url=f"https://www.ensembl.org/id/{stable_id}",
                annotations={
                    "biotype": info.get("biotype"),
                    "object_type": info.get("object_type"),
                    "assembly_name": info.get("assembly_name"),
                },
            )
            for key, value in defaults.items():
                if getattr(ps, key, None) is None:
                    setattr(ps, key, value)
            parsed.append(ps)
    finally:
        if owns:
            await conn.aclose()

    logger.info("ensembl fetch: %d record(s) parsed", len(parsed))
    return parsed


async def ingest(
    stable_ids: list[str],
    *,
    kind: str = "genomic",
    batch_size: int = 200,
) -> ImportReport:
    records = await fetch_records(stable_ids, kind=kind)
    return await import_with_run(
        records,
        source_key="ensembl",
        kind="fetch_ids",
        params={"stable_ids": stable_ids, "kind": kind},
        batch_size=batch_size,
    )
