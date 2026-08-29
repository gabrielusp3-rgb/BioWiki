"""Live SQL integrity checks. None of these call external scientific APIs."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import OrganismGroup, SequenceType
from app.models.features import (
    CrisprFeature,
    DnaFeature,
    ProteinFeature,
    RnaFeature,
    VirusFeature,
)
from app.models.organism import Organism
from app.models.publication import Publication, SequenceReference
from app.models.sequence import Sequence
from app.pipeline.validation import infer_group_from_lineage
from app.schemas.statistics import IntegrityCheck


async def _count_group_having(session: AsyncSession, *columns) -> int:
    rows = (
        await session.execute(
            select(*columns).group_by(*columns).having(func.count() > 1)
        )
    ).all()
    return len(rows)


async def sql_integrity_checks(session: AsyncSession) -> list[IntegrityCheck]:
    checks: list[IntegrityCheck] = []

    dup_seq = await _count_group_having(
        session, Sequence.source_id, Sequence.accession, Sequence.version
    )
    checks.append(
        IntegrityCheck(
            name="sequences:unique_source_accession_version",
            ok=dup_seq == 0,
            detail="natural key source+accession+version is unique",
            expected=0,
            actual=dup_seq,
        )
    )

    dup_tax = await _count_group_having(session, Organism.tax_id)
    checks.append(
        IntegrityCheck(
            name="organisms:unique_tax_id",
            ok=dup_tax == 0,
            detail="each TaxID is stored once",
            expected=0,
            actual=dup_tax,
        )
    )

    dup_pmid = int(
        (
            await session.execute(
                select(func.count())
                .select_from(
                    select(Publication.pubmed_id)
                    .where(Publication.pubmed_id.is_not(None))
                    .group_by(Publication.pubmed_id)
                    .having(func.count() > 1)
                    .subquery()
                )
            )
        ).scalar_one()
    )
    checks.append(
        IntegrityCheck(
            name="publications:unique_pmid",
            ok=dup_pmid == 0,
            detail="one PubMed ID maps to one publication row",
            expected=0,
            actual=dup_pmid,
        )
    )

    orphan_seq = int(
        (
            await session.execute(
                select(func.count())
                .select_from(SequenceReference)
                .outerjoin(Sequence, SequenceReference.sequence_id == Sequence.id)
                .where(Sequence.id.is_(None))
            )
        ).scalar_one()
    )
    checks.append(
        IntegrityCheck(
            name="references:sequence_id_exists",
            ok=orphan_seq == 0,
            detail="every SequenceReference.sequence_id points to a sequence",
            expected=0,
            actual=orphan_seq,
        )
    )

    orphan_pub = int(
        (
            await session.execute(
                select(func.count())
                .select_from(SequenceReference)
                .outerjoin(Publication, SequenceReference.publication_id == Publication.id)
                .where(Publication.id.is_(None))
            )
        ).scalar_one()
    )
    checks.append(
        IntegrityCheck(
            name="references:publication_id_exists",
            ok=orphan_pub == 0,
            detail="every SequenceReference.publication_id points to a publication",
            expected=0,
            actual=orphan_pub,
        )
    )

    feature_pairs = (
        (DnaFeature, SequenceType.DNA, "dna_features"),
        (RnaFeature, SequenceType.RNA, "rna_features"),
        (CrisprFeature, SequenceType.CRISPR, "crispr_features"),
        (VirusFeature, SequenceType.VIRUS, "virus_features"),
    )
    feature_mismatch = 0
    for feature_cls, expected, label in feature_pairs:
        n = int(
            (
                await session.execute(
                    select(func.count())
                    .select_from(feature_cls)
                    .join(Sequence, Sequence.id == feature_cls.sequence_id)
                    .where(Sequence.seq_type != expected)
                )
            ).scalar_one()
        )
        feature_mismatch += n
        checks.append(
            IntegrityCheck(
                name=f"features:{label}_match_seq_type",
                ok=n == 0,
                detail=f"{label} only attach to {expected.value} sequences",
                expected=0,
                actual=n,
            )
        )

    protein_mismatch = int(
        (
            await session.execute(
                select(func.count())
                .select_from(ProteinFeature)
                .join(Sequence, Sequence.id == ProteinFeature.sequence_id)
                .where(Sequence.seq_type.notin_([SequenceType.PROTEIN, SequenceType.PEPTIDE]))
            )
        ).scalar_one()
    )
    checks.append(
        IntegrityCheck(
            name="features:protein_features_match_seq_type",
            ok=protein_mismatch == 0,
            detail="protein_features only attach to protein or peptide sequences",
            expected=0,
            actual=protein_mismatch,
        )
    )

    genome_seq = int(
        (
            await session.execute(
                select(func.count()).where(Sequence.seq_type == SequenceType.GENOME)
            )
        ).scalar_one()
    )
    checks.append(
        IntegrityCheck(
            name="genome:assemblies_not_duplicated_as_sequences",
            ok=genome_seq == 0,
            detail="genome catalogue is genome_records; SequenceType.GENOME stays unused",
            expected=0,
            actual=genome_seq,
        )
    )

    organisms = list((await session.execute(select(Organism))).scalars().all())
    group_mismatch = 0
    bacteria_without_lineage = 0
    empty_lineage = 0
    for org in organisms:
        lineage = list(org.lineage or [])
        if not lineage:
            empty_lineage += 1
            if org.group == OrganismGroup.BACTERIA:
                bacteria_without_lineage += 1
            continue
        inferred = infer_group_from_lineage(lineage)
        if inferred and inferred != org.group.value:
            group_mismatch += 1

    checks.append(
        IntegrityCheck(
            name="taxonomy:group_matches_lineage",
            ok=group_mismatch == 0,
            detail="stored organism.group matches lineage when lineage can classify a group",
            expected=0,
            actual=group_mismatch,
        )
    )
    checks.append(
        IntegrityCheck(
            name="taxonomy:no_silent_bacteria_fallback",
            ok=bacteria_without_lineage == 0,
            detail="bacteria is never stored without a lineage that can support it",
            expected=0,
            actual=bacteria_without_lineage,
        )
    )
    checks.append(
        IntegrityCheck(
            name="taxonomy:empty_lineage_count",
            ok=True,
            detail="organisms currently missing lineage (informational; not corruption)",
            expected=None,
            actual=empty_lineage,
        )
    )

    pubs = int((await session.execute(select(func.count()).select_from(Publication))).scalar_one())
    linked = int(
        (
            await session.execute(
                select(func.count(func.distinct(SequenceReference.publication_id)))
            )
        ).scalar_one()
    )
    checks.append(
        IntegrityCheck(
            name="publications:linked_within_total",
            ok=linked <= pubs,
            detail="linked publications never exceed stored publications; unlinked may be legitimate",
            expected=pubs,
            actual=linked,
        )
    )
    checks.append(
        IntegrityCheck(
            name="publications:unlinked_are_not_corruption",
            ok=True,
            detail="publications without SequenceReference are counted, not failed",
            expected=pubs,
            actual=pubs - linked,
        )
    )

    return checks
