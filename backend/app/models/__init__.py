"""SQLAlchemy models. Importing this package registers every table."""

from app.database.base import Base
from app.models.category import Category
from app.models.cross_reference import SequenceCrossReference
from app.models.download import Download
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
from app.models.genome import GenomeRecord
from app.models.ingestion import IngestionRun
from app.models.organism import Organism
from app.models.paleogenomics import (
    PaleogenomicClaim,
    PaleogenomicClaimSource,
    PaleogenomicIntrogressionRegion,
    PaleogenomicProfile,
    PaleogenomicProject,
    PaleogenomicPublicationMembership,
    PaleogenomicSequenceMembership,
)
from app.models.publication import Publication, SequenceReference
from app.models.sequence import Sequence
from app.models.source import DataSource
from app.models.taxonomy import Taxonomy

__all__ = [
    "Base",
    "Category",
    "SequenceCrossReference",
    "Download",
    "CrisprFeature",
    "DnaFeature",
    "ProteinDomain",
    "ProteinFeature",
    "ProteinPdbRef",
    "RnaFeature",
    "VirusFeature",
    "Gene",
    "GenomeRecord",
    "IngestionRun",
    "Organism",
    "PaleogenomicClaim",
    "PaleogenomicClaimSource",
    "PaleogenomicIntrogressionRegion",
    "PaleogenomicProfile",
    "PaleogenomicProject",
    "PaleogenomicPublicationMembership",
    "PaleogenomicSequenceMembership",
    "Publication",
    "SequenceReference",
    "Sequence",
    "DataSource",
    "Taxonomy",
]
