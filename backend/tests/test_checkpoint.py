"""Checkpoint resume behaviour: completed jobs stay skipped; failures retry."""

from __future__ import annotations

from app.pipeline.models import ImportReport
from scripts.expand_dataset import _source_job_failed


def test_completed_jobs_are_not_source_failures() -> None:
    report = ImportReport(total=5, created=5, updated=0, skipped=0, failed=0)
    assert _source_job_failed(report) is False


def test_rfam_unavailable_report_is_retryable_failure() -> None:
    report = ImportReport(
        failed=1,
        errors=["rfam RF00001: source unavailable (Record not found.)."],
    )
    assert _source_job_failed(report) is True
