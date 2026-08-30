"""Convert ORM rows into API read schemas (flattening related data)."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.models.genome import GenomeRecord
from app.models.organism import Organism
from app.models.publication import Publication
from app.models.sequence import Sequence
from app.schemas.genome import GenomeRead
from app.schemas.organism import OrganismRead
from app.schemas.publication import PublicationDetail, PublicationRead
from app.schemas.sequence import (
    CrisprRead,
    DnaRead,
    ProteinRead,
    RnaRead,
    SequenceBase,
    VirusRead,
)


def _f(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def _organism_name(seq: Sequence) -> str:
    org = seq.organism
    return org.scientific_name if org else ""


def _tax_id(seq: Sequence) -> int | None:
    return seq.organism.tax_id if seq.organism else None


def _source_name(obj: Sequence | GenomeRecord) -> str:
    return obj.source.name if obj.source else ""


def _base_kwargs(seq: Sequence, *, with_residues: bool) -> dict[str, Any]:
    return {
        "id": seq.id,
        "type": seq.seq_type.value,
        "accession": seq.accession,
        "version": seq.version,
        "name": seq.name,
        "organism": _organism_name(seq),
        "tax_id": _tax_id(seq),
        "source": _source_name(seq),
        "length": seq.length,
        "updated_at": seq.updated_at,
        "sequence": seq.residues if with_residues else None,
        "description": seq.description,
        "gene_name": seq.gene_name,
        "chromosome": seq.chromosome,
        "source_url": seq.source_url,
        "annotations": seq.annotations,
    }


def to_dna(seq: Sequence, *, with_residues: bool = True) -> DnaRead:
    feat = seq.dna_feature
    return DnaRead(
        **_base_kwargs(seq, with_residues=with_residues),
        molecule_type=feat.molecule_type if feat else None,
        strand=feat.strand if feat else None,
        gc_content=_f(seq.gc_content),
    )


def to_rna(seq: Sequence, *, with_residues: bool = True) -> RnaRead:
    feat = seq.rna_feature
    from app.models.enums import RnaClass

    return RnaRead(
        **_base_kwargs(seq, with_residues=with_residues),
        rna_class=feat.rna_class if feat else RnaClass.OTHER,
        is_coding=feat.is_coding if feat else False,
        gc_content=_f(seq.gc_content),
    )


def to_protein(seq: Sequence, *, with_residues: bool = True) -> ProteinRead:
    feat = seq.protein_feature
    return ProteinRead(
        **_base_kwargs(seq, with_residues=with_residues),
        gene=feat.gene if feat else None,
        reviewed=feat.reviewed if feat else False,
        molecular_weight=_f(feat.molecular_weight) if feat else None,
        function=feat.function if feat else None,
        pdb_ids=[r.pdb_id for r in (seq.pdb_refs or [])],
        domains=[d.name for d in (seq.protein_domains or [])],
    )


def to_virus(seq: Sequence, *, with_residues: bool = True) -> VirusRead:
    feat = seq.virus_feature
    from app.models.enums import GenomeType

    return VirusRead(
        **_base_kwargs(seq, with_residues=with_residues),
        family=feat.family if feat else "Unclassified",
        host=feat.host if feat else None,
        genome_type=feat.genome_type if feat else GenomeType.OTHER,
        segment=feat.segment if feat else None,
        molecule=(seq.molecule.value if seq.molecule else "dna"),
        gc_content=_f(seq.gc_content),
    )


def to_crispr(seq: Sequence, *, with_residues: bool = True) -> CrisprRead:
    feat = seq.crispr_feature
    from app.models.enums import CasSystem, CrisprEvidenceType

    return CrisprRead(
        id=seq.id,
        accession=seq.accession,
        name=seq.name,
        organism=_organism_name(seq),
        tax_id=_tax_id(seq),
        source=_source_name(seq),
        system=feat.cas_system if feat else CasSystem.OTHER,
        evidence_type=(
            feat.evidence_type if feat else CrisprEvidenceType.NATURAL_CRISPR_ELEMENT
        ),
        target_gene=(feat.target_gene if feat and feat.target_gene else seq.gene_name or ""),
        pam=(feat.pam if feat and feat.pam else ""),
        guide_length=seq.length,
        guide_sequence=seq.residues if with_residues else None,
        genomic_target=feat.genomic_target if feat else None,
        on_target_score=_f(feat.on_target_score) if feat else None,
        off_target_score=_f(feat.off_target_score) if feat else None,
        target_source_accession=feat.target_source_accession if feat else None,
        target_tax_id=feat.target_tax_id if feat else None,
        source_pmid=feat.source_pmid if feat else None,
        method=feat.method if feat else None,
        updated_at=seq.updated_at,
        description=seq.description,
        source_url=seq.source_url,
        gc_content=_f(seq.gc_content),
        annotations=seq.annotations,
    )


def to_sequence(seq: Sequence, *, with_residues: bool = True) -> SequenceBase:
    from app.models.enums import SequenceType

    dispatch = {
        SequenceType.DNA: to_dna,
        SequenceType.GENOME: to_dna,
        SequenceType.RNA: to_rna,
        SequenceType.PROTEIN: to_protein,
        SequenceType.PEPTIDE: to_protein,
        SequenceType.VIRUS: to_virus,
        SequenceType.CRISPR: to_crispr,
    }
    fn = dispatch.get(seq.seq_type, to_dna)
    return fn(seq, with_residues=with_residues)


def to_organism(org: Organism, paleogenomic_slug: str | None = None) -> OrganismRead:
    return OrganismRead(
        id=org.id,
        slug=org.slug,
        scientific_name=org.scientific_name,
        common_name=org.common_name,
        tax_id=org.tax_id,
        rank=org.rank,
        lineage=list(org.lineage or []),
        group=org.group,
        image_url=org.image_url,
        sequence_count=org.sequence_count,
        extinction_status=org.extinction_status,
        extinction_date_text=org.extinction_date_text,
        geologic_period=org.geologic_period,
        paleogenomic_slug=paleogenomic_slug,
    )


def to_genome(g: GenomeRecord) -> GenomeRead:
    return GenomeRead(
        id=g.id,
        accession=g.accession,
        assembly_name=g.assembly_name,
        description=g.description,
        organism=g.organism.scientific_name if g.organism else "",
        tax_id=g.organism.tax_id if g.organism else 0,
        source=_source_name(g),
        assembly_level=g.assembly_level,
        total_length=g.total_length,
        chromosome_count=g.chromosome_count,
        scaffold_count=g.scaffold_count,
        contig_count=g.contig_count,
        gc_content=_f(g.gc_content),
        release_date=g.release_date,
        source_url=g.source_url,
        updated_at=g.updated_at,
    )


def to_publication(pub: Publication) -> PublicationRead:
    return PublicationRead(
        id=pub.id,
        pubmed_id=pub.pubmed_id,
        doi=pub.doi,
        pmc_id=pub.pmc_id,
        title=pub.title,
        abstract=pub.abstract,
        authors=list(pub.authors or []),
        journal=pub.journal,
        year=pub.year,
        volume=pub.volume,
        pages=pub.pages,
        url=pub.url,
    )


def to_publication_detail(
    pub: Publication, accessions: list[str]
) -> PublicationDetail:
    base = to_publication(pub).model_dump(by_alias=False)
    return PublicationDetail(**base, sequence_accessions=accessions)
