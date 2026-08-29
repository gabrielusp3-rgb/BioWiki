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
