"""Persistence of real genome assembly records (``genome_records``).

Upserts are keyed by the assembly accession (globally unique at NCBI). All
metadata comes verbatim from the source report; aggregates missing at the
source stay NULL.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import AssemblyLevel
from app.models.genome import GenomeRecord
from app.pipeline.errors import ValidationError
from app.pipeline.importers.sequence_importer import SequenceImporter
from app.pipeline.models import ParsedGenome

_LEVELS = {level.value for level in AssemblyLevel}


def _parse_release_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def validate_genome(pg: ParsedGenome) -> None:
    if not (pg.accession and pg.accession.strip()):
        raise ValidationError("genome accession is required", field="accession")
    if not (pg.source_key and pg.source_key.strip()):
        raise ValidationError("genome source_key is required", field="source_key")
    org = pg.organism
    if org is None or not (org.scientific_name and org.scientific_name.strip()):
        raise ValidationError("genome organism is required", field="organism")
    if not (isinstance(org.tax_id, int) and org.tax_id > 0):
        raise ValidationError("organism.tax_id must be a positive integer", field="organism.tax_id")
    if pg.assembly_level is not None and pg.assembly_level not in _LEVELS:
        raise ValidationError(
            f"assembly_level must be one of {sorted(_LEVELS)}", field="assembly_level"
        )


class GenomeImporter:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self._sequence_importer = SequenceImporter(session)

    async def upsert_genome(self, pg: ParsedGenome) -> tuple[GenomeRecord, bool]:
        validate_genome(pg)

        source = await self._sequence_importer.upsert_source(pg.source_key, pg.source_name)
        organism = await self._sequence_importer.upsert_organism(pg.organism)

        existing = (
            await self.session.execute(
                select(GenomeRecord).where(GenomeRecord.accession == pg.accession)
            )
        ).scalar_one_or_none()

        created = existing is None
        record = existing or GenomeRecord(accession=pg.accession)

        record.assembly_name = (
            pg.assembly_name[:200] if pg.assembly_name and len(pg.assembly_name) > 200 else pg.assembly_name
        )
        record.description = pg.description
        record.organism_id = organism.id
        record.source_id = source.id
        record.assembly_level = AssemblyLevel(pg.assembly_level or "contig")
        record.total_length = pg.total_length
        record.chromosome_count = pg.chromosome_count
        record.scaffold_count = pg.scaffold_count
        record.contig_count = pg.contig_count
        record.gc_content = pg.gc_content
        record.release_date = _parse_release_date(pg.release_date)
        record.source_url = (
            pg.source_url[:500] if pg.source_url and len(pg.source_url) > 500 else pg.source_url
        )
        record.annotations = pg.annotations

        if created:
            self.session.add(record)
        await self.session.flush()
        return record, created
