"""Python enums mirroring the PostgreSQL ENUM types (values match exactly)."""

from __future__ import annotations

import enum

from sqlalchemy import Enum as SAEnum


class SequenceType(str, enum.Enum):
    DNA = "dna"
    RNA = "rna"
    PROTEIN = "protein"
    CRISPR = "crispr"
    VIRUS = "virus"
    GENOME = "genome"
    PEPTIDE = "peptide"


class Molecule(str, enum.Enum):
    DNA = "dna"
    RNA = "rna"
    PROTEIN = "protein"


class DnaMoleculeType(str, enum.Enum):
    GENE = "gene"
    CDS = "cds"
    GENOMIC = "genomic"
    MRNA = "mrna"
    EXON = "exon"
    REGULATORY = "regulatory"
    OTHER = "other"


class Strand(str, enum.Enum):
    PLUS = "+"
    MINUS = "-"
    UNKNOWN = "unknown"


class RnaClass(str, enum.Enum):
    MRNA = "mrna"
    TRNA = "trna"
    RRNA = "rrna"
    LNCRNA = "lncrna"
    MIRNA = "mirna"
    SNRNA = "snrna"
    OTHER = "other"


class CasSystem(str, enum.Enum):
    CAS9 = "cas9"
    CAS12A = "cas12a"
    CAS13 = "cas13"
    BASE_EDITOR = "base_editor"
    OTHER = "other"


class CrisprEvidenceType(str, enum.Enum):
    """How a CRISPR catalogue row was obtained.

    These are not interchangeable biological entities:
    a natural spacer is not an engineered guide, and a PAM scan is not
    experimental validation.
    """

    NATURAL_CRISPR_ELEMENT = "natural_crispr_element"
    EXPERIMENTAL_GUIDE = "experimental_guide"
    COMPUTATIONAL_TARGET = "computational_target"


class GenomeType(str, enum.Enum):
    DSDNA = "dsDNA"
    SSDNA = "ssDNA"
    DSRNA = "dsRNA"
    SSRNA_PLUS = "ssRNA+"
    SSRNA_MINUS = "ssRNA-"
    SSRNA_RT = "ssRNA-RT"
    DSDNA_RT = "dsDNA-RT"
    OTHER = "other"


class OrganismGroup(str, enum.Enum):
    ANIMAL = "animal"
    PLANT = "plant"
    FUNGUS = "fungus"
    BACTERIA = "bacteria"
    ARCHAEA = "archaea"
    VIRUS = "virus"
    PROTOZOAN = "protozoan"


class AssemblyLevel(str, enum.Enum):
    COMPLETE = "complete"
    CHROMOSOME = "chromosome"
    SCAFFOLD = "scaffold"
    CONTIG = "contig"


class ExtinctionStatus(str, enum.Enum):
    """Optional organism status. Living taxa keep this NULL."""

    EXTINCT = "extinct"
    EXTINCT_PREHISTORIC = "extinct_prehistoric"
    EXTINCT_HISTORIC = "extinct_historic"
    ARCHAIC_HOMININ = "archaic_hominin"


class PaleogenomicSubsection(str, enum.Enum):
    EXTINCT_SPECIES = "extinct_species"
    ARCHAIC_HOMININ = "archaic_hominin"
    ANCIENT_DNA = "ancient_dna"
    ARCHAIC_INTROGRESSION = "archaic_introgression"


class EvidenceLevel(str, enum.Enum):
    CONSENSUS = "consensus"
    STRONG_EVIDENCE = "strong_evidence"
    SUPPORTED_HYPOTHESIS = "supported_hypothesis"
    DEBATED = "debated"
    UNKNOWN = "unknown"


class DeextinctionStatus(str, enum.Enum):
    NO_ACTIVE_PROGRAM = "no_active_program"
    RESEARCH_DISCUSSION = "research_discussion"
    ACTIVE_RESEARCH_PROGRAM = "active_research_program"
    GENOME_ENGINEERING_RESEARCH = "genome_engineering_research"
    REPRODUCTIVE_TECHNOLOGY_RESEARCH = "reproductive_technology_research"
    PROXY_TRAIT_ENGINEERING = "proxy_trait_engineering"
    REINTRODUCTION_PLANNING = "reintroduction_planning"
    UNKNOWN = "unknown"


class ArchaicSource(str, enum.Enum):
    NEANDERTHAL = "neanderthal"
    DENISOVAN = "denisovan"
    UNKNOWN_ARCHAIC = "unknown_archaic"


class PaleogenomicRecordKind(str, enum.Enum):
    MITOCHONDRIAL = "mitochondrial"
    NUCLEAR = "nuclear"
    GENE = "gene"
    CONTIG = "contig"
    OTHER = "other"


def pg_enum(python_enum: type[enum.Enum], name: str) -> SAEnum:
    """Bind a Python enum to an existing PostgreSQL ENUM type (never recreated)."""
    return SAEnum(
        python_enum,
        name=name,
        native_enum=True,
        create_type=False,
        values_callable=lambda e: [member.value for member in e],
    )


SEQUENCE_TYPE_ENUM = pg_enum(SequenceType, "sequence_type")
MOLECULE_ENUM = pg_enum(Molecule, "molecule")
DNA_MOLECULE_TYPE_ENUM = pg_enum(DnaMoleculeType, "dna_molecule_type")
STRAND_ENUM = pg_enum(Strand, "strand")
RNA_CLASS_ENUM = pg_enum(RnaClass, "rna_class")
CAS_SYSTEM_ENUM = pg_enum(CasSystem, "cas_system")
CRISPR_EVIDENCE_TYPE_ENUM = pg_enum(CrisprEvidenceType, "crispr_evidence_type")
GENOME_TYPE_ENUM = pg_enum(GenomeType, "genome_type")
ORGANISM_GROUP_ENUM = pg_enum(OrganismGroup, "organism_group")
ASSEMBLY_LEVEL_ENUM = pg_enum(AssemblyLevel, "assembly_level")
