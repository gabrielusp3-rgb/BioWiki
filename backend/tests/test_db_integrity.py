"""Read-only PostgreSQL integrity checks against the live scientific dataset.

These tests SELECT only. They never INSERT/UPDATE/DELETE production rows.
"""

from __future__ import annotations

import pytest
from sqlalchemy import func, select, text

from app.database.session import get_sessionmaker
from app.models.enums import SequenceType
from app.models.organism import Organism
from app.models.publication import Publication, SequenceReference
from app.models.sequence import Sequence
from app.models.source import DataSource
from app.pipeline.validation import pubmed_id_is_valid
from app.services import sync_service
from scripts.seed_initial import (
    DNA_ACCESSIONS,
    GENOME_ACCESSIONS,
    PROTEIN_ACCESSIONS,
    RNA_ACCESSIONS,
    VIRUS_ACCESSIONS,
)

pytestmark = pytest.mark.live

ORIGINAL_CURATED = (
    DNA_ACCESSIONS + RNA_ACCESSIONS + PROTEIN_ACCESSIONS + VIRUS_ACCESSIONS
)


async def test_database_connection() -> None:
    async with get_sessionmaker()() as session:
        value = (await session.execute(text("SELECT 1"))).scalar_one()
    assert value == 1


async def test_live_counts() -> None:
    async with get_sessionmaker()() as session:
        sequences = int((await session.execute(select(func.count(Sequence.id)))).scalar_one())
        publications = int(
            (await session.execute(select(func.count(Publication.id)))).scalar_one()
        )
        organisms = int((await session.execute(select(func.count(Organism.id)))).scalar_one())
        links = int(
            (await session.execute(select(func.count(SequenceReference.id)))).scalar_one()
        )
    assert sequences == 1542
    assert publications == 5838
    assert organisms == 454
    assert links == 6198


async def test_no_duplicate_sequence_keys() -> None:
    async with get_sessionmaker()() as session:
        dupes = (
            await session.execute(
                select(Sequence.accession, Sequence.source_id, Sequence.version)
                .group_by(Sequence.accession, Sequence.source_id, Sequence.version)
                .having(func.count() > 1)
            )
        ).all()
    assert dupes == []


async def test_accessions_and_sources_present() -> None:
    async with get_sessionmaker()() as session:
        empty_acc = int(
            (
                await session.execute(
                    select(func.count()).where(
                        (Sequence.accession.is_(None)) | (Sequence.accession == "")
                    )
                )
            ).scalar_one()
        )
        missing_source = int(
            (
                await session.execute(
                    select(func.count())
                    .select_from(Sequence)
                    .outerjoin(DataSource, Sequence.source_id == DataSource.id)
                    .where(DataSource.id.is_(None))
                )
            ).scalar_one()
        )
        empty_residue_rows = (
            await session.execute(
                select(Sequence.accession, Sequence.seq_type, Sequence.length).where(
                    (Sequence.residues.is_(None)) | (Sequence.residues == "")
                )
            )
        ).all()
    assert empty_acc == 0
    assert missing_source == 0
    assert empty_residue_rows == [], (
        "sequences without residues (NCBI CONTIG records must be filled via FASTA): "
        f"{[row[0] for row in empty_residue_rows]}"
    )


async def test_pubmed_ids_are_valid_when_present() -> None:
    async with get_sessionmaker()() as session:
        pmids = list(
            (
                await session.execute(
                    select(Publication.pubmed_id).where(Publication.pubmed_id.is_not(None))
                )
            )
            .scalars()
            .all()
        )
    assert pmids
    assert all(pubmed_id_is_valid(int(pmid)) for pmid in pmids)


async def test_integrity_service_passes() -> None:
    async with get_sessionmaker()() as session:
        report = await sync_service.check_integrity(session)
    assert report.ok is True
    assert report.checks
    assert all(check.ok for check in report.checks)


async def test_original_curated_accessions_preserved() -> None:
    async with get_sessionmaker()() as session:
        stored = set(
            (
                await session.execute(
                    select(Sequence.accession).where(Sequence.accession.in_(ORIGINAL_CURATED))
                )
            )
            .scalars()
            .all()
        )
    missing = [acc for acc in ORIGINAL_CURATED if acc not in stored]
    assert missing == [], f"original curated accessions missing: {missing}"


async def test_original_genome_assemblies_preserved() -> None:
    from app.models.genome import GenomeRecord

    async with get_sessionmaker()() as session:
        stored = set(
            (
                await session.execute(
                    select(GenomeRecord.accession).where(
                        GenomeRecord.accession.in_(GENOME_ACCESSIONS)
                    )
                )
            )
            .scalars()
            .all()
        )
        genome_seq = int(
            (
                await session.execute(
                    select(func.count()).where(Sequence.seq_type == SequenceType.GENOME)
                )
            ).scalar_one()
        )
        assemblies = int(
            (await session.execute(select(func.count()).select_from(GenomeRecord))).scalar_one()
        )
    missing = [acc for acc in GENOME_ACCESSIONS if acc not in stored]
    assert missing == []
    assert genome_seq == 0
    assert assemblies == 32


async def test_named_records_still_present() -> None:
    async with get_sessionmaker()() as session:
        nm = (
            await session.execute(
                select(Sequence).where(Sequence.accession == "NM_000207").limit(1)
            )
        ).scalar_one_or_none()
        insulin = (
            await session.execute(
                select(Sequence).where(Sequence.accession == "P01308").limit(1)
            )
        ).scalar_one_or_none()
        crispr = (
            await session.execute(
                select(Sequence).where(Sequence.seq_type == "crispr").limit(1)
            )
        ).scalar_one_or_none()
    assert nm is not None
    assert insulin is not None
    assert crispr is not None


_REPRESENTATIVE_NG = ("NG_074726", "NG_047936", "NG_048025")


async def test_no_empty_ng_star_residues() -> None:
    async with get_sessionmaker()() as session:
        empty_ng = list(
            (
                await session.execute(
                    select(Sequence.accession).where(
                        Sequence.accession.startswith("NG_"),
                        (Sequence.residues.is_(None)) | (Sequence.residues == ""),
                    )
                )
            )
            .scalars()
            .all()
        )
    assert empty_ng == []


async def test_residues_length_matches_stored_length() -> None:
    async with get_sessionmaker()() as session:
        mismatches = (
            await session.execute(
                select(Sequence.accession, Sequence.length).where(
                    Sequence.residues.is_not(None),
                    Sequence.residues != "",
                    func.char_length(Sequence.residues) != Sequence.length,
                )
            )
        ).all()
    assert mismatches == [], f"length mismatches: {mismatches[:10]}"


async def test_checksum_matches_residues() -> None:
    import hashlib

    async with get_sessionmaker()() as session:
        rows = (
            await session.execute(
                select(Sequence.accession, Sequence.residues, Sequence.checksum).where(
                    Sequence.residues.is_not(None),
                    Sequence.residues != "",
                )
            )
        ).all()
    bad = []
    for accession, residues, checksum in rows:
        expected = hashlib.sha256(residues.encode("ascii", "ignore")).hexdigest()
        if checksum != expected:
            bad.append(accession)
    assert bad == [], f"checksum mismatches: {bad[:10]}"


async def test_gc_content_matches_residues_for_nucleotides() -> None:
    from app.pipeline.validation import compute_gc

    nucleotide = {
        SequenceType.DNA,
        SequenceType.RNA,
        SequenceType.CRISPR,
        SequenceType.VIRUS,
        SequenceType.GENOME,
    }
    async with get_sessionmaker()() as session:
        rows = (
            await session.execute(
                select(
                    Sequence.accession,
                    Sequence.seq_type,
                    Sequence.residues,
                    Sequence.gc_content,
                ).where(
                    Sequence.residues.is_not(None),
                    Sequence.residues != "",
                    Sequence.seq_type.in_(nucleotide),
                )
            )
        ).all()
    bad = []
    for accession, seq_type, residues, gc_content in rows:
        expected = compute_gc(residues)
        if expected is None:
            continue
        if gc_content is None or abs(float(gc_content) - expected) > 0.00015:
            bad.append(accession)
    assert bad == [], f"gc_content mismatches: {bad[:10]}"


async def test_representative_ng_records_have_sequence() -> None:
    async with get_sessionmaker()() as session:
        rows = {
            row.accession: row
            for row in (
                await session.execute(
                    select(Sequence).where(Sequence.accession.in_(_REPRESENTATIVE_NG))
                )
            )
            .scalars()
            .all()
        }
    missing = [acc for acc in _REPRESENTATIVE_NG if acc not in rows]
    assert missing == []
    for acc in _REPRESENTATIVE_NG:
        seq = rows[acc]
        assert seq.residues, acc
        assert len(seq.residues) == int(seq.length), acc
        assert seq.checksum
        assert seq.gc_content is not None

