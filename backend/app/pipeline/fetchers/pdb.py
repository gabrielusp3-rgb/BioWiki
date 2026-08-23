"""RCSB PDB fetcher: entry + polymer entities → protein/nucleic records.

Each polymer entity becomes one sequence record (accession ``{PDB}_{entity}``)
with its real canonical sequence, source organism, gene names and the entry's
primary citation (PubMed/DOI).
"""

from __future__ import annotations

from typing import Any

from app.pipeline.fetchers.base import import_with_run
from app.pipeline.logging import get_logger
from app.pipeline.models import (
    ImportReport,
    ParsedOrganism,
    ParsedPublication,
    ParsedSequence,
    ParsedXref,
)
from app.services.connectors.errors import ConnectorNotFound
from app.services.connectors.pdb import PDBConnector

logger = get_logger("biowiki.pipeline.fetchers.pdb")

_POLYMER_TYPE_MAP = {
    "Protein": ("protein", "protein"),
    "DNA": ("dna", "dna"),
    "RNA": ("rna", "rna"),
}


def _entry_publications(entry: dict[str, Any]) -> list[ParsedPublication]:
    publications: list[ParsedPublication] = []
    for order, citation in enumerate(entry.get("citation") or [], start=1):
        title = citation.get("title")
        pubmed_raw = citation.get("pdbx_database_id_pub_med")
        pubmed_id = int(pubmed_raw) if pubmed_raw and str(pubmed_raw).isdigit() else None
        if not title and not pubmed_id:
            continue
        publications.append(
            ParsedPublication(
                title=title,
                pubmed_id=pubmed_id,
                doi=citation.get("pdbx_database_id_doi"),
                authors=list(citation.get("rcsb_authors") or []),
                journal=citation.get("journal_abbrev"),
                year=citation.get("year"),
                volume=str(citation.get("journal_volume") or "") or None,
                pages=(
                    f"{citation.get('page_first')}-{citation.get('page_last')}"
                    if citation.get("page_first") and citation.get("page_last")
                    else None
                ),
                url=f"https://pubmed.ncbi.nlm.nih.gov/{pubmed_id}/" if pubmed_id else None,
                reference_order=order,
            )
        )
    return publications


def _entity_to_parsed(
    pdb_id: str,
    entity_id: str,
    entity: dict[str, Any],
    entry: dict[str, Any],
) -> ParsedSequence | None:
    poly = entity.get("entity_poly") or {}
    polymer_type = poly.get("rcsb_entity_polymer_type")
    mapped = _POLYMER_TYPE_MAP.get(polymer_type or "")
    if mapped is None:
        return None
    seq_type, molecule = mapped

    residues = (poly.get("pdbx_seq_one_letter_code_can") or "").replace("\n", "").strip().upper()
    if not residues:
        return None

    organisms = entity.get("rcsb_entity_source_organism") or []
    organism_data = organisms[0] if organisms and isinstance(organisms[0], dict) else {}
    tax_id = organism_data.get("ncbi_taxonomy_id")
    scientific_name = organism_data.get("ncbi_scientific_name")
    if not tax_id or not scientific_name:
        logger.warning("pdb: %s_%s lacks source organism; skipped", pdb_id, entity_id)
        return None

    gene_name = None
    gene_entries = organism_data.get("rcsb_gene_name") or []
    if gene_entries and isinstance(gene_entries[0], dict):
        gene_name = gene_entries[0].get("value")

    entity_info = entity.get("rcsb_polymer_entity") or {}
    struct = entry.get("struct") or {}
    name = entity_info.get("pdbx_description") or struct.get("title") or f"{pdb_id} entity {entity_id}"

    ps = ParsedSequence(
        seq_type=seq_type,
        accession=f"{pdb_id}_{entity_id}",
        name=name,
        organism=ParsedOrganism(
            scientific_name=scientific_name, tax_id=int(tax_id)
        ),
        source_key="pdb",
        source_name="RCSB PDB",
        description=struct.get("title"),
        molecule=molecule,
        residues=residues,
        gene=gene_name,
        gene_name=gene_name,
        reviewed=False,
        pdb_ids=[pdb_id],
        source_url=f"https://www.rcsb.org/structure/{pdb_id}",
        cross_references=[
            ParsedXref(
                db_name="pdb",
                external_id=pdb_id,
                url=f"https://www.rcsb.org/structure/{pdb_id}",
            )
        ],
        publications=_entry_publications(entry),
    )
    if seq_type == "dna":
        ps.molecule_type = "other"
    elif seq_type == "rna":
        ps.rna_class = "other"
    return ps


async def fetch_records(
    pdb_ids: list[str],
    *,
    connector: PDBConnector | None = None,
) -> list[ParsedSequence]:
    if not pdb_ids:
        raise ValueError("Provide at least one PDB ID.")

    owns = connector is None
    conn = connector or PDBConnector()
    parsed: list[ParsedSequence] = []
    try:
        for raw_id in dict.fromkeys(p.strip().upper() for p in pdb_ids if p.strip()):
            try:
                entry = await conn.get_entry(raw_id)
            except ConnectorNotFound:
                logger.warning("pdb: entry %s not found at RCSB; skipped", raw_id)
                continue
            identifiers = entry.get("rcsb_entry_container_identifiers") or {}
            entity_ids = identifiers.get("polymer_entity_ids") or []
            for entity_id in entity_ids:
                try:
                    entity = await conn.get_polymer_entity(raw_id, str(entity_id))
                except ConnectorNotFound:
                    logger.warning("pdb: entity %s_%s not found; skipped", raw_id, entity_id)
                    continue
                record = _entity_to_parsed(raw_id, str(entity_id), entity, entry)
                if record is not None:
                    parsed.append(record)
    finally:
        if owns:
            await conn.aclose()

    logger.info("pdb fetch: %d record(s) parsed", len(parsed))
    return parsed


async def ingest(pdb_ids: list[str], *, batch_size: int = 200) -> ImportReport:
    records = await fetch_records(pdb_ids)
    return await import_with_run(
        records,
        source_key="pdb",
        kind="fetch_entries",
        params={"pdb_ids": pdb_ids},
        batch_size=batch_size,
    )
