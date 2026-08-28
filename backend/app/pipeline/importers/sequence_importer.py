"""Persistence of validated :class:`ParsedSequence` records.

Idempotent upserts keyed by natural identifiers:
- data source by ``key``
- organism by ``tax_id``
- gene by ``(organism_id, symbol)``
- publication by PubMed ID / DOI / title
- sequence by ``(source_id, accession, version)``; a version bump updates the
  existing row (incremental update) instead of duplicating the accession, and
  unchanged checksums are detected so re-imports stay cheap.

Feature rows and normalised children (PDB refs, domains, cross-references,
bibliographic references) are kept in sync on update. All writes flow through a
caller-provided session so the worker controls transaction/batch boundaries.
"""

from __future__ import annotations

import re

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cross_reference import SequenceCrossReference
from app.models.enums import (
    CasSystem,
    DnaMoleculeType,
    GenomeType,
    Molecule,
    OrganismGroup,
    RnaClass,
    SequenceType,
    Strand,
)
from app.models.features import (
    CrisprFeature,
    DnaFeature,
    ProteinDomain,
    ProteinFeature,
    ProteinPdbRef,
    RnaFeature,
    VirusFeature,
)
from app.models.gene import Gene
from app.models.organism import Organism
from app.models.publication import SequenceReference
from app.models.sequence import Sequence
from app.models.source import DataSource
from app.pipeline.errors import ValidationError
from app.pipeline.models import ParsedOrganism, ParsedSequence
from app.pipeline.validation import infer_group_from_lineage, normalize_lineage

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _slugify(value: str) -> str:
    return _SLUG_RE.sub("-", value.strip().lower()).strip("-")


def _clip(value: str | None, max_len: int) -> str | None:
    """Fit a real source string into an existing VARCHAR column.

    Residues are never clipped. Truncation is only applied to display/metadata
    fields whose schema length is smaller than some genuine GenBank titles.
    The full original text is kept in ``description`` (TEXT) when the name is
    shortened.
    """
    if value is None:
        return None
    text = value.strip()
    if not text:
        return None
    return text if len(text) <= max_len else text[:max_len]


class SequenceImporter:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert_source(self, key: str, name: str | None) -> DataSource:
        existing = (
            await self.session.execute(select(DataSource).where(DataSource.key == key))
        ).scalar_one_or_none()
        if existing:
            if name and existing.name != name:
                existing.name = name
            return existing
        source = DataSource(key=key, name=name or key)
        self.session.add(source)
        await self.session.flush()
        return source

    async def upsert_organism(self, parsed: ParsedOrganism) -> Organism:
        existing = (
            await self.session.execute(
                select(Organism).where(Organism.tax_id == parsed.tax_id)
            )
        ).scalar_one_or_none()

        lineage = normalize_lineage(parsed.lineage)
        group = OrganismGroup(parsed.group) if parsed.group else None
        if group is None and lineage:
            inferred = infer_group_from_lineage(lineage)
            if inferred:
                group = OrganismGroup(inferred)
        if existing:
            scientific_name = _clip(parsed.scientific_name, 300)
            existing.scientific_name = scientific_name or existing.scientific_name
            if parsed.common_name:
                existing.common_name = _clip(parsed.common_name, 300)
            if group is not None:
                existing.group = group
            if lineage:
                existing.lineage = lineage
            if parsed.rank:
                existing.rank = parsed.rank
            if parsed.image_url:
                existing.image_url = _clip(parsed.image_url, 500)
            return existing

        slug = _slugify(parsed.scientific_name) or f"tax-{parsed.tax_id}"
        clash = (
            await self.session.execute(select(Organism).where(Organism.slug == slug))
        ).scalar_one_or_none()
        if clash:
            slug = f"{slug}-{parsed.tax_id}"

        if group is None:
            raise ValidationError(
                "organism.group could not be determined from source taxonomy; "
                "refusing to invent a kingdom",
                field="organism.group",
            )

        organism = Organism(
            slug=slug[:160],
            scientific_name=_clip(parsed.scientific_name, 300) or parsed.scientific_name,
            common_name=_clip(parsed.common_name, 300),
            tax_id=parsed.tax_id,
            rank=parsed.rank,
            lineage=lineage or None,
            group=group,
            image_url=_clip(parsed.image_url, 500),
        )
        self.session.add(organism)
        await self.session.flush()
        return organism

    async def upsert_gene(
        self, organism: Organism, symbol: str, chromosome: str | None
    ) -> Gene:
        cleaned = _clip(symbol.strip(), 64) or symbol.strip()[:64]
        existing = (
            await self.session.execute(
                select(Gene).where(
                    Gene.organism_id == organism.id, Gene.symbol == cleaned
                )
            )
        ).scalar_one_or_none()
        if existing:
            if chromosome and not existing.chromosome:
                existing.chromosome = _clip(chromosome, 32)
            return existing
        gene = Gene(
            symbol=cleaned,
            organism_id=organism.id,
            chromosome=_clip(chromosome, 32),
        )
        self.session.add(gene)
        await self.session.flush()
        return gene

    async def upsert_sequence(self, ps: ParsedSequence) -> tuple[Sequence, bool]:
        source = await self.upsert_source(ps.source_key, ps.source_name)
        organism = await self.upsert_organism(ps.organism)

        existing = (
            await self.session.execute(
                select(Sequence).where(
                    Sequence.source_id == source.id,
                    Sequence.accession == ps.accession,
                    Sequence.version == ps.version,
                )
            )
        ).scalar_one_or_none()
        if existing is None and ps.version is not None:
            # Incremental update: a new version of an accession replaces the
            # previous row instead of creating a duplicate record.
            existing = (
                await self.session.execute(
                    select(Sequence)
                    .where(
                        Sequence.source_id == source.id,
                        Sequence.accession == ps.accession,
                    )
                    .order_by(Sequence.updated_at.desc())
                    .limit(1)
                )
            ).scalar_one_or_none()

        created = existing is None
        seq = existing or Sequence(accession=ps.accession, version=ps.version)

        seq.seq_type = SequenceType(ps.seq_type)
        seq.molecule = Molecule(ps.molecule) if ps.molecule else None
        seq.accession = _clip(ps.accession, 64) or ps.accession
        seq.version = _clip(ps.version, 16)
        full_name = (ps.name or "").strip()
        seq.name = full_name[:500] if full_name else ps.accession
        seq.description = ps.description or (full_name if len(full_name) > 500 else None)
        seq.organism_id = organism.id
        seq.source_id = source.id
        seq.length = ps.effective_length()
        seq.residues = ps.residues
        seq.checksum = ps.checksum()
        seq.gc_content = ps.gc_content
        seq.source_updated_at = ps.source_updated_at
        seq.chromosome = _clip(ps.chromosome, 32)
        seq.source_url = _clip(ps.source_url, 500)
        seq.annotations = ps.annotations

        gene_symbol = _clip(ps.gene_name or ps.gene, 120)
        seq.gene_name = gene_symbol
        if gene_symbol:
            gene = await self.upsert_gene(organism, gene_symbol, ps.chromosome)
            seq.gene_id = gene.id
        else:
            seq.gene_id = None

        if created:
            self.session.add(seq)
        await self.session.flush()

        await self._apply_feature(seq, ps)
        await self._apply_children(seq, ps)
        await self._apply_publications(seq, ps)
        return seq, created

    async def _apply_feature(self, seq: Sequence, ps: ParsedSequence) -> None:
        st = seq.seq_type
        keep = {
            SequenceType.DNA: DnaFeature,
            SequenceType.GENOME: DnaFeature,
            SequenceType.RNA: RnaFeature,
            SequenceType.PROTEIN: ProteinFeature,
            SequenceType.PEPTIDE: ProteinFeature,
            SequenceType.CRISPR: CrisprFeature,
            SequenceType.VIRUS: VirusFeature,
        }.get(st)
        for model in (DnaFeature, RnaFeature, ProteinFeature, CrisprFeature, VirusFeature):
            if model is not keep:
                await self.session.execute(delete(model).where(model.sequence_id == seq.id))
        if st not in (SequenceType.PROTEIN, SequenceType.PEPTIDE):
            await self.session.execute(
                delete(ProteinPdbRef).where(ProteinPdbRef.sequence_id == seq.id)
            )
            await self.session.execute(
                delete(ProteinDomain).where(ProteinDomain.sequence_id == seq.id)
            )

        if st == SequenceType.DNA or st == SequenceType.GENOME:
            feat = await self.session.get(DnaFeature, seq.id) or DnaFeature(sequence_id=seq.id)
            feat.molecule_type = DnaMoleculeType(ps.molecule_type or "other")
            feat.strand = Strand(ps.strand or "unknown")
            await self._merge(feat)
        elif st == SequenceType.RNA:
            feat = await self.session.get(RnaFeature, seq.id) or RnaFeature(sequence_id=seq.id)
            feat.rna_class = RnaClass(ps.rna_class or "other")
            feat.is_coding = bool(ps.is_coding)
            await self._merge(feat)
        elif st == SequenceType.CRISPR:
            feat = await self.session.get(CrisprFeature, seq.id) or CrisprFeature(sequence_id=seq.id)
            feat.cas_system = CasSystem(ps.cas_system or "other")
            feat.target_gene = _clip(ps.target_gene, 120)
            feat.pam = _clip(ps.pam, 16)
            feat.genomic_target = _clip(ps.genomic_target, 120)
            feat.on_target_score = ps.on_target_score
            feat.off_target_score = ps.off_target_score
            await self._merge(feat)
        elif st == SequenceType.VIRUS:
            feat = await self.session.get(VirusFeature, seq.id) or VirusFeature(sequence_id=seq.id)
            feat.family = _clip(ps.family, 160) or ""
            feat.host = _clip(ps.host, 300)
            feat.genome_type = GenomeType(ps.genome_type or "other")
            feat.segment = _clip(ps.segment, 64)
            await self._merge(feat)
        elif st in (SequenceType.PROTEIN, SequenceType.PEPTIDE):
            feat = await self.session.get(ProteinFeature, seq.id) or ProteinFeature(sequence_id=seq.id)
            feat.gene = _clip(ps.gene, 120)
            feat.reviewed = bool(ps.reviewed)
            feat.molecular_weight = ps.molecular_weight
            feat.function = ps.function
            await self._merge(feat)

    async def _merge(self, feature) -> None:
        # session.get returns attached instances; only add genuinely new ones.
        # Never touch seq.<relationship> here — unloaded relationships would
        # trigger a synchronous lazy load, which is illegal in async SQLAlchemy.
        if feature not in self.session:
            self.session.add(feature)
        await self.session.flush()

    async def _apply_children(self, seq: Sequence, ps: ParsedSequence) -> None:
        if seq.seq_type in (SequenceType.PROTEIN, SequenceType.PEPTIDE):
            await self.session.execute(
                delete(ProteinPdbRef).where(ProteinPdbRef.sequence_id == seq.id)
            )
            await self.session.execute(
                delete(ProteinDomain).where(ProteinDomain.sequence_id == seq.id)
            )
            for pdb_id in dict.fromkeys(ps.pdb_ids):
                self.session.add(ProteinPdbRef(sequence_id=seq.id, pdb_id=pdb_id))
            for name in dict.fromkeys(ps.domains):
                clipped = _clip(name, 200)
                if clipped:
                    self.session.add(ProteinDomain(sequence_id=seq.id, name=clipped))

        if ps.cross_references:
            await self.session.execute(
                delete(SequenceCrossReference).where(
                    SequenceCrossReference.sequence_id == seq.id
                )
            )
            seen = set()
            for xref in ps.cross_references:
                key = (xref.db_name, xref.external_id)
                if not xref.db_name or not xref.external_id or key in seen:
                    continue
                seen.add(key)
                self.session.add(
                    SequenceCrossReference(
                        sequence_id=seq.id,
                        db_name=xref.db_name,
                        external_id=xref.external_id,
                        url=xref.url,
                    )
                )
        await self.session.flush()

    async def _apply_publications(self, seq: Sequence, ps: ParsedSequence) -> None:
        """Sync sequence↔publication links from the record's real references."""
        if not ps.publications:
            return
        await self.session.execute(
            delete(SequenceReference).where(SequenceReference.sequence_id == seq.id)
        )
        seen_publication_ids: set = set()
        for parsed_pub in ps.publications:
            publication = await upsert_publication(self.session, parsed_pub)
            if publication is None or publication.id in seen_publication_ids:
                continue
            seen_publication_ids.add(publication.id)
            self.session.add(
                SequenceReference(
                    sequence_id=seq.id,
                    publication_id=publication.id,
                    reference_order=parsed_pub.reference_order,
                )
            )
        await self.session.flush()
