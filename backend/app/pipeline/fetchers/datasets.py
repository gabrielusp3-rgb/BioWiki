"""NCBI Datasets fetcher: genome assembly reports → ``genome_records``.

Assembly-level provenance follows the accession itself: GCF_* is RefSeq,
GCA_* is GenBank. Aggregates (length, chromosome counts, GC) are copied from
the real assembly stats; anything the report omits stays NULL.
"""

from __future__ import annotations

from typing import Any

from app.pipeline.errors import ValidationError
from app.pipeline.importers.genome_importer import GenomeImporter
from app.pipeline.logging import get_logger
from app.pipeline.models import ImportReport, ParsedGenome, ParsedOrganism
from app.pipeline.run_log import record_run
from app.database.session import get_sessionmaker
from app.pipeline.taxonomy import group_from_taxonomy, parse_ncbi_taxonomy_xml
from app.services.connectors.datasets import NCBIDatasetsConnector

logger = get_logger("biowiki.pipeline.fetchers.datasets")

_LEVEL_MAP = {
    "complete genome": "complete",
    "chromosome": "chromosome",
    "scaffold": "scaffold",
    "contig": "contig",
}



def _report_to_parsed(report: dict[str, Any]) -> ParsedGenome | None:
    accession = report.get("accession")
    organism_data = report.get("organism") or {}
    tax_id = organism_data.get("tax_id")
    organism_name = organism_data.get("organism_name")
    if not accession or not tax_id or not organism_name:
        return None

    assembly_info = report.get("assembly_info") or {}
    stats = report.get("assembly_stats") or {}

    def _to_int(value: Any) -> int | None:
        try:
            return int(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    gc_percent = stats.get("gc_percent")
    gc_content = None
    if isinstance(gc_percent, (int, float)) and 0 <= gc_percent <= 100:
        gc_content = round(float(gc_percent) / 100.0, 4)

    level_raw = str(assembly_info.get("assembly_level", "")).strip().lower()
    is_refseq = accession.upper().startswith("GCF_")

    return ParsedGenome(
        accession=accession,
        organism=ParsedOrganism(
            scientific_name=organism_name,
            tax_id=int(tax_id),
            common_name=organism_data.get("common_name"),
        ),
        source_key="ncbi_refseq" if is_refseq else "ncbi_genbank",
        source_name="NCBI RefSeq" if is_refseq else "NCBI GenBank",
        assembly_name=assembly_info.get("assembly_name"),
        assembly_level=_LEVEL_MAP.get(level_raw),
        description=assembly_info.get("description")
        or f"{organism_name} assembly {assembly_info.get('assembly_name') or accession}",
        total_length=_to_int(stats.get("total_sequence_length")),
        chromosome_count=_to_int(stats.get("total_number_of_chromosomes")),
        scaffold_count=_to_int(stats.get("number_of_scaffolds")),
        contig_count=_to_int(stats.get("number_of_contigs")),
        gc_content=gc_content,
        release_date=assembly_info.get("release_date"),
        source_url=f"https://www.ncbi.nlm.nih.gov/datasets/genome/{accession}/",
        annotations={
            "assembly_type": assembly_info.get("assembly_type"),
            "submitter": assembly_info.get("submitter"),
            "sequencing_tech": assembly_info.get("sequencing_tech"),
        },
    )


async def fetch_reports(
    accessions: list[str] | None = None,
    *,
    taxon: str | None = None,
    limit: int = 20,
    connector: NCBIDatasetsConnector | None = None,
) -> list[ParsedGenome]:
    if not accessions and not taxon:
        raise ValueError("Provide assembly accessions or a taxon.")

    owns = connector is None
    conn = connector or NCBIDatasetsConnector()
    parsed: list[ParsedGenome] = []
    try:
        raw_reports: list[dict[str, Any]] = []
        if accessions:
            raw_reports.extend(await conn.assembly_reports(accessions))
        if taxon:
            token: str | None = None
            while len(raw_reports) < limit:
                page, token = await conn.assemblies_for_taxon(
                    taxon, page_size=min(50, limit - len(raw_reports)), page_token=token
                )
                raw_reports.extend(page)
                if not token or not page:
                    break

        for report in raw_reports[: limit if taxon else None]:
            genome = _report_to_parsed(report)
            if genome is not None:
                parsed.append(genome)
            else:
                logger.warning("datasets: report without accession/organism skipped")
    finally:
        if owns:
            await conn.aclose()

    logger.info("datasets fetch: %d assembly report(s) parsed", len(parsed))
    await _annotate_taxonomy(parsed)
    return parsed


async def _annotate_taxonomy(genomes: list[ParsedGenome]) -> None:
    """Fill organism lineage and group from NCBI Taxonomy (official records)."""
    tax_ids = list(
        dict.fromkeys(
            str(g.organism.tax_id)
            for g in genomes
            if g.organism and g.organism.tax_id and (not g.organism.group or not g.organism.lineage)
        )
    )
    if not tax_ids:
        return

    from app.pipeline.fetchers.base import chunked
    from app.services.connectors.ncbi import NCBIConnector

    lookup: dict[int, dict] = {}
    async with NCBIConnector() as conn:
        for group in chunked(tax_ids, 40):
            try:
                xml = await conn.efetch(
                    "taxonomy", list(group), rettype="xml", retmode="xml"
                )
                lookup.update(parse_ncbi_taxonomy_xml(xml))
            except Exception:
                logger.exception("taxonomy efetch failed for %d tax id(s)", len(group))
                continue

    for genome in genomes:
        if genome.organism is None:
            continue
        doc = lookup.get(int(genome.organism.tax_id))
        if not doc:
            continue
        lineage = doc.get("lineage") or []
        if lineage and not genome.organism.lineage:
            genome.organism.lineage = lineage
        if doc.get("common_name") and not genome.organism.common_name:
            genome.organism.common_name = str(doc["common_name"])
        if doc.get("rank") and not genome.organism.rank:
            genome.organism.rank = str(doc["rank"])
        if not genome.organism.group:
            genome.organism.group = group_from_taxonomy(
                lineage=genome.organism.lineage,
                division=doc.get("division"),
            )


async def ingest(
    accessions: list[str] | None = None,
    *,
    taxon: str | None = None,
    limit: int = 20,
) -> ImportReport:
    genomes = await fetch_reports(accessions, taxon=taxon, limit=limit)

    async with record_run(
        "ncbi_datasets",
        "fetch_assemblies",
        {"accessions": accessions, "taxon": taxon, "limit": limit},
    ) as run:
        report = ImportReport()
        async with get_sessionmaker()() as session:
            importer = GenomeImporter(session)
            for genome in genomes:
                report.total += 1
                try:
                    async with session.begin_nested():
                        _, created = await importer.upsert_genome(genome)
                    if created:
                        report.created += 1
                    else:
                        report.updated += 1
                except ValidationError as exc:
                    report.skipped += 1
                    report.errors.append(f"skip {genome.accession}: {exc}")
                    logger.warning("skip %s: %s", genome.accession, exc)
                except Exception as exc:  # noqa: BLE001 — isolate per-record failures
                    report.failed += 1
                    report.errors.append(f"fail {genome.accession}: {exc}")
                    logger.exception("fail %s", genome.accession)
            await session.commit()
        run.set_report(report)

    # Keep cached UI counters aligned after writing genome rows.
    if report.created or report.updated:
        from app.services.sync_service import refresh_counts_safely

        await refresh_counts_safely()

    logger.info("datasets import finished: %s", report.as_dict())
    return report
