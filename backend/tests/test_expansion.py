"""Expansion targets, CRISPR evidence, Cas9 NGG scan, pagination at >10k."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.models.enums import CrisprEvidenceType
from app.pipeline.errors import ValidationError
from app.pipeline.expansion.cas9_ngg import find_cas9_ngg_sites
from app.pipeline.expansion.checkpoint import load_checkpoint, save_checkpoint
from app.pipeline.expansion.diversity import (
    build_sequence_jobs,
    build_shortfall_jobs,
    summarize_plan,
)
from app.pipeline.expansion.targets import (
    publication_remaining,
    sequence_ceiling,
    species_new_cap,
    species_over_new_cap,
)
from app.pipeline.validation import validate
from app.services.pagination import decode_cursor, encode_cursor
from scripts.expand_dataset import _source_job_failed
from tests.fixtures import make_fixture_crispr


def test_sequence_target_is_additional_not_total() -> None:
    assert sequence_ceiling(1542, 10000) == 11542
    assert sequence_ceiling(1542, 0) == 1542


def test_publication_target_is_total_not_additional() -> None:
    assert publication_remaining(5838, 25000) == 19162
    assert publication_remaining(25000, 25000) == 0
    assert publication_remaining(26000, 25000) == 0


def test_species_cap_is_guardrail_on_new_records() -> None:
    cap = species_new_cap(10000, fraction=0.03)
    assert cap == 300
    assert species_over_new_cap(562, {562: 300}, 10000) is True
    assert species_over_new_cap(562, {562: 12}, 10000) is False


def test_jobs_scale_with_additional_sequences() -> None:
    small = summarize_plan(build_sequence_jobs(200))
    large = summarize_plan(build_sequence_jobs(10000))
    assert large["jobs"] >= small["jobs"]
    assert large["estimated_fetch_ceiling"] > small["estimated_fetch_ceiling"]
    assert large["taxa_seeded"] >= 170
    assert large["estimated_fetch_ceiling"] >= 18000
    assert large["virus_families"] >= 35


def test_protein_and_crispr_jobs_do_not_start_with_model_organisms() -> None:
    jobs = build_sequence_jobs(10000)
    protein = [job for job in jobs if job.get("category") == "protein"]
    crispr = [job for job in jobs if job.get("category") == "crispr"]
    assert protein[0]["id"] != "prot-homo-sapiens"
    assert any(job["id"] == "prot-homo-sapiens" for job in protein)
    assert crispr[0]["id"] != "crispr-escherichia-coli"
    assert any(job["id"] == "crispr-escherichia-coli" for job in crispr)


def test_shortfall_jobs_do_not_repeat_main_plan() -> None:
    main_ids = {job["id"] for job in build_sequence_jobs(10000)}
    fill = build_shortfall_jobs(2500)
    fill_ids = {job["id"] for job in fill}
    assert fill
    assert fill_ids.isdisjoint(main_ids)
    assert any(job.get("category") == "dna" for job in fill)
    assert any(job.get("category") == "protein" for job in fill)


def test_category_filter_limits_plan() -> None:
    jobs = build_sequence_jobs(1000, categories={"virus"})
    cats = {j.get("category") for j in jobs}
    assert "virus" in cats
    assert "dna" not in cats
    assert "protein" not in cats
    assert "rna" not in cats


def test_cas9_ngg_copies_authentic_spacer() -> None:
    # 20 nt spacer ATGC... + NGG
    spacer = "ATGCCATGCCATGCCATGCC"
    seq = spacer + "AGG" + "TTTT"
    sites = find_cas9_ngg_sites(seq, max_sites=3)
    assert sites
    plus = [s for s in sites if s.strand == "+"]
    assert plus
    assert plus[0].spacer == spacer
    assert plus[0].pam == "AGG"
    assert plus[0].start == 0


def test_natural_crispr_is_the_default_evidence() -> None:
    ps = make_fixture_crispr()
    validate(ps)
    assert ps.evidence_type == CrisprEvidenceType.NATURAL_CRISPR_ELEMENT.value


def test_computational_crispr_requires_target_and_forbids_invented_scores() -> None:
    ps = make_fixture_crispr(
        evidence_type="computational_target",
        target_source_accession="NC_007596",
        target_tax_id=37349,
        method="cas9_NGG_spacer20",
        on_target_score=0.9,
        off_target_score=None,
    )
    with pytest.raises(ValidationError, match="invent efficiency scores"):
        validate(ps)
    ps.on_target_score = None
    validate(ps)


def test_computational_without_target_accession_is_rejected() -> None:
    ps = make_fixture_crispr(evidence_type="computational_target", method="cas9_NGG_spacer20")
    with pytest.raises(ValidationError, match="target accession"):
        validate(ps)


def test_experimental_guide_requires_provenance() -> None:
    ps = make_fixture_crispr(evidence_type="experimental_guide")
    with pytest.raises(ValidationError, match="publication or source URL"):
        validate(ps)
    ps.source_pmid = 24336571
    validate(ps)


def test_checkpoint_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "expansion_checkpoint.json"
    data = load_checkpoint(path)
    data["job_id"] = "dna-human"
    data["inserted"] = 3
    save_checkpoint(path, data)
    loaded = load_checkpoint(path)
    assert loaded["job_id"] == "dna-human"
    assert loaded["inserted"] == 3
    assert "ncbi_api_key" not in loaded
    assert "DATABASE_URL" not in loaded


def test_source_failure_report_is_retryable() -> None:
    from app.pipeline.models import ImportReport

    ok = ImportReport(total=5, created=5)
    assert _source_job_failed(ok) is False
    failed = ImportReport(failed=1, errors=["ncbi timeout"])
    assert _source_job_failed(failed) is True


def test_sequence_importer_resolves_publication_upsert() -> None:
    from app.pipeline.importers.sequence_importer import upsert_publication

    assert callable(upsert_publication)


def test_pagination_cursors_above_10k() -> None:
    for offset in (0, 20, 10000, 11542, 25000):
        assert decode_cursor(encode_cursor(offset)) == offset
    page1 = encode_cursor(0 + 20)
    page2 = encode_cursor(20 + 20)
    assert decode_cursor(page1) == 20
    assert decode_cursor(page2) == 40
    assert decode_cursor(page1) != decode_cursor(page2)


def test_dna_cannot_starve_protein() -> None:
    from app.pipeline.expansion.scheduler import schedule_jobs, skip_status

    jobs = [
        {"id": "dna-a", "category": "dna", "kind": "ncbi"},
        {"id": "dna-b", "category": "dna", "kind": "ncbi"},
        {"id": "prot-a", "category": "protein", "kind": "uniprot"},
        {"id": "virus-a", "category": "virus", "kind": "ncbi"},
        {"id": "crispr-a", "category": "crispr", "kind": "ncbi"},
    ]
    counts = {"dna": 5761, "rna": 2556, "protein": 0, "virus": 0, "crispr": 0}
    scheduled, deferred = schedule_jobs(jobs, new_by_category=counts)
    assert {job["id"] for job in deferred} == {"dna-a", "dna-b"}
    assert [job["id"] for job in scheduled] == ["prot-a", "virus-a", "crispr-a"]
    assert skip_status({"id": "prot-a", "category": "protein"}, new_by_category=counts) is None
    assert skip_status({"id": "dna-a", "category": "dna"}, new_by_category=counts) == (
        "DEFERRED_CATEGORY_OVERFILLED"
    )


def test_rna_cannot_starve_virus() -> None:
    from app.pipeline.expansion.scheduler import schedule_jobs, skip_status

    jobs = [
        {"id": "rna-a", "category": "rna", "kind": "ncbi"},
        {"id": "virus-a", "category": "virus", "kind": "ncbi"},
    ]
    counts = {"dna": 5761, "rna": 2556, "protein": 0, "virus": 0, "crispr": 0}
    scheduled, deferred = schedule_jobs(jobs, new_by_category=counts)
    assert [job["id"] for job in scheduled] == ["virus-a"]
    assert [job["id"] for job in deferred] == ["rna-a"]
    assert skip_status({"id": "virus-a", "category": "virus"}, new_by_category=counts) is None


def test_dna_rna_cannot_starve_crispr_or_computational_job() -> None:
    from app.pipeline.expansion.scheduler import schedule_jobs, skip_status

    jobs = [
        {"id": "dna-a", "category": "dna", "kind": "ncbi"},
        {"id": "rna-a", "category": "rna", "kind": "ncbi"},
        {"id": "crispr-a", "category": "crispr", "kind": "ncbi"},
        {"id": "crispr-computational-ngg", "category": "crispr", "kind": "computational_ngg"},
    ]
    counts = {"dna": 8000, "rna": 4000, "protein": 0, "virus": 0, "crispr": 0}
    scheduled, deferred = schedule_jobs(jobs, new_by_category=counts)
    assert {job["id"] for job in deferred} == {"dna-a", "rna-a"}
    assert [job["id"] for job in scheduled] == ["crispr-a", "crispr-computational-ngg"]
    stats = {"sequences": 20000}
    assert (
        skip_status(
            {"id": "crispr-computational-ngg", "kind": "computational_ngg", "category": "crispr"},
            new_by_category=counts,
            stats=stats,
            additional=10000,
            ceiling=11558,
        )
        is None
    )


def test_global_soft_target_cannot_stop_underfilled_categories() -> None:
    from app.pipeline.expansion.scheduler import skip_status

    counts = {"dna": 5761, "rna": 2556, "protein": 0, "virus": 0, "crispr": 0}
    stats = {"sequences": 20000}
    for job in (
        {"id": "prot-x", "category": "protein", "kind": "uniprot"},
        {"id": "virus-x", "category": "virus", "kind": "ncbi"},
        {"id": "crispr-x", "category": "crispr", "kind": "ncbi"},
        {"id": "asm-x", "category": "genome", "kind": "genomes"},
    ):
        assert skip_status(job, new_by_category=counts, stats=stats, ceiling=11558) is None


def test_deferred_job_is_not_marked_completed() -> None:
    from app.pipeline.expansion.checkpoint import (
        DEFERRED_CATEGORY_OVERFILLED,
        default_checkpoint,
        job_is_done,
        set_job_status,
    )

    checkpoint = default_checkpoint()
    set_job_status(checkpoint, "rna-left", DEFERRED_CATEGORY_OVERFILLED, category="rna")
    assert "rna-left" not in checkpoint["completed"]
    assert job_is_done(checkpoint, "rna-left") is False


def test_commit_before_checkpoint_reconcile_is_idempotent() -> None:
    from app.pipeline.expansion.checkpoint import (
        apply_succeeded_runs,
        default_checkpoint,
        job_is_done,
    )

    checkpoint = default_checkpoint()
    checkpoint["inserted"] = 8273
    checkpoint["new_by_category"] = {"dna": 5749, "rna": 2524}
    runs = [
        {
            "job_id": "rna-paramecium-tetraurelia",
            "status": "succeeded",
            "created": 28,
            "updated": 0,
            "skipped": 0,
            "total": 28,
            "finished_at": "2026-08-29T13:12:46Z",
        }
    ]
    first = apply_succeeded_runs(
        checkpoint, runs, job_categories={"rna-paramecium-tetraurelia": "rna"}
    )
    assert first == ["rna-paramecium-tetraurelia"]
    assert job_is_done(checkpoint, "rna-paramecium-tetraurelia") is True
    assert checkpoint["inserted"] == 8301
    assert checkpoint["new_by_category"]["rna"] == 2552
    second = apply_succeeded_runs(
        checkpoint, runs, job_categories={"rna-paramecium-tetraurelia": "rna"}
    )
    assert second == []
    assert checkpoint["inserted"] == 8301


def test_category_aware_shortfall_skips_overfilled_dna_rna() -> None:
    from app.pipeline.expansion.diversity import build_shortfall_jobs
    from app.pipeline.expansion.scheduler import deficient_categories, schedule_jobs

    counts = {"dna": 5761, "rna": 2556, "protein": 0, "virus": 0, "crispr": 0}
    cats = deficient_categories(counts)
    assert "dna" not in cats
    assert "rna" not in cats
    assert cats == {"protein", "virus", "crispr"}
    jobs = build_shortfall_jobs(3000, categories=cats)
    assert jobs
    assert all(job["category"] in {"protein", "virus", "crispr"} for job in jobs)
    scheduled, deferred = schedule_jobs(jobs, new_by_category=counts)
    assert not deferred
    assert any(job["category"] == "protein" for job in scheduled)
    assert any(job["category"] == "virus" for job in scheduled)
    assert any(job["category"] == "crispr" for job in scheduled)


def test_genome_jobs_are_not_sequence_type_genome() -> None:
    jobs = build_sequence_jobs(10000, categories={"genome"}, sources={"genomes"})
    assert jobs
    assert all(job["kind"] == "genomes" for job in jobs)
    assert all(job.get("seq_type") != "genome" for job in jobs)
    assert all(job.get("category") == "genome" for job in jobs)


def test_legacy_completed_without_report_is_not_success() -> None:
    from app.pipeline.expansion.checkpoint import (
        DEFERRED_CATEGORY_OVERFILLED,
        migrate_checkpoint,
    )

    data = {
        "completed": ["dna-skipped-by-ceiling"],
        "reports": [],
        "job_status": {},
    }
    migrated = migrate_checkpoint(data)
    assert "dna-skipped-by-ceiling" not in migrated["completed"]
    assert (
        migrated["job_status"]["dna-skipped-by-ceiling"]["status"]
        == DEFERRED_CATEGORY_OVERFILLED
    )


def test_pubmed_jobs_are_not_demoted_without_report() -> None:
    from app.pipeline.expansion.checkpoint import (
        COMPLETED_SUCCESSFULLY,
        migrate_checkpoint,
    )

    data = {
        "completed": ["pubmed-elink-all", "pm-crispr"],
        "reports": [],
        "job_status": {},
    }
    migrated = migrate_checkpoint(data)
    assert "pubmed-elink-all" in migrated["completed"]
    assert "pm-crispr" in migrated["completed"]
    assert migrated["job_status"]["pubmed-elink-all"]["status"] == COMPLETED_SUCCESSFULLY


def test_completed_job_is_not_demoted_when_category_frozen() -> None:
    from app.pipeline.expansion.checkpoint import (
        COMPLETED_SUCCESSFULLY,
        DEFERRED_CATEGORY_OVERFILLED,
        default_checkpoint,
        job_is_done,
        set_job_status,
    )

    checkpoint = default_checkpoint()
    set_job_status(
        checkpoint,
        "rna-tetrahymena-thermophila",
        COMPLETED_SUCCESSFULLY,
        category="rna",
        records_created=28,
    )
    set_job_status(
        checkpoint,
        "rna-tetrahymena-thermophila",
        DEFERRED_CATEGORY_OVERFILLED,
        category="rna",
        reason="category already over its planned NEW share",
    )
    assert (
        checkpoint["job_status"]["rna-tetrahymena-thermophila"]["status"]
        == COMPLETED_SUCCESSFULLY
    )
    assert "rna-tetrahymena-thermophila" in checkpoint["completed"]
    assert job_is_done(checkpoint, "rna-tetrahymena-thermophila") is True


def test_empty_successful_job_is_skipped_already_present() -> None:
    from app.pipeline.expansion.checkpoint import (
        SKIPPED_ALREADY_PRESENT,
        default_checkpoint,
        job_is_done,
        set_job_status,
    )

    checkpoint = default_checkpoint()
    set_job_status(
        checkpoint,
        "prot-already-there",
        SKIPPED_ALREADY_PRESENT,
        category="protein",
        records_skipped=12,
    )
    assert "prot-already-there" in checkpoint["completed"]
    assert job_is_done(checkpoint, "prot-already-there") is True


def test_crisprcasdb_is_not_scraped() -> None:
    from app.pipeline.expansion.crisprcasdb import crisprcasdb_integration_status

    status = crisprcasdb_integration_status()
    assert status["status"] == "EXTERNAL_LIMITATION"
