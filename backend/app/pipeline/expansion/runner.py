"""Run a biodiversity expansion: fetch → filter → ingest → checkpoint."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.database.session import get_sessionmaker
from app.models.enums import CrisprEvidenceType, SequenceType
from app.models.genome import GenomeRecord
from app.models.organism import Organism
from app.models.publication import Publication, SequenceReference
from app.models.sequence import Sequence
from app.models.source import DataSource
from app.pipeline.expansion.cas9_ngg import find_cas9_ngg_sites
from app.pipeline.expansion.checkpoint import (
    add_new_tax,
    default_checkpoint,
    load_checkpoint,
    save_checkpoint,
    tax_counts,
)
from app.pipeline.expansion.diversity import (
    CATEGORY_SHARES,
    COMPUTATIONAL_TAX_IDS,
    DEFAULT_MAX_LENGTHS,
    PUBMED_SEARCHES,
    build_sequence_jobs,
    summarize_plan,
)
from app.pipeline.expansion.targets import (
    publication_remaining,
    sequence_ceiling,
    species_over_new_cap,
)
from app.pipeline.fetchers import datasets, ncbi, pubmed, rfam, uniprot
from app.pipeline.fetchers.base import import_with_run
from app.pipeline.models import ImportReport, ParsedOrganism, ParsedSequence

COMPUTATIONAL_SOURCE_KEY = "biowiki_computational"
COMPUTATIONAL_METHOD = "cas9_NGG_spacer20"


def _source_job_failed(report: ImportReport) -> bool:
    """True when a job produced no persisted records and reported a source failure."""
    return (
        report.failed > 0
        and report.created == 0
        and report.updated == 0
        and report.skipped == 0
    )


def _merge(target: ImportReport, part: ImportReport) -> None:
    target.total += part.total
    target.created += part.created
    target.updated += part.updated
    target.skipped += part.skipped
    target.failed += part.failed
    target.errors.extend(part.errors)


def _show(label: str, report: ImportReport) -> None:
    print(
        f"  {label:<40} total={report.total:<5} created={report.created:<5} "
        f"updated={report.updated:<5} skipped={report.skipped:<5} failed={report.failed}"
    )
    for error in report.errors[:4]:
        print(f"      ! {error}")
    if len(report.errors) > 4:
        print(f"      ! … and {len(report.errors) - 4} more")


async def snapshot() -> dict[str, Any]:
    async with get_sessionmaker()() as session:
        by_type = {
            (seq_type.value if hasattr(seq_type, "value") else str(seq_type)): int(count)
            for seq_type, count in (
                await session.execute(
                    select(Sequence.seq_type, func.count(Sequence.id)).group_by(Sequence.seq_type)
                )
            ).all()
        }
        by_source = {
            str(key): int(count)
            for key, count in (
                await session.execute(
                    select(DataSource.key, func.count(Sequence.id))
                    .join(Sequence, Sequence.source_id == DataSource.id)
                    .group_by(DataSource.key)
                )
            ).all()
        }
        by_group = {
            (group.value if hasattr(group, "value") else str(group)): int(count)
            for group, count in (
                await session.execute(
                    select(Organism.group, func.count(Organism.id)).group_by(Organism.group)
                )
            ).all()
        }
        dup_rows = (
            await session.execute(
                select(Sequence.accession, Sequence.source_id, Sequence.version)
                .group_by(Sequence.accession, Sequence.source_id, Sequence.version)
                .having(func.count() > 1)
            )
        ).all()
        pmid_count = int(
            (
                await session.execute(
                    select(func.count(func.distinct(Publication.pubmed_id))).where(
                        Publication.pubmed_id.is_not(None)
                    )
                )
            ).scalar_one()
        )
        return {
            "sequences": int((await session.execute(select(func.count(Sequence.id)))).scalar_one()),
            "by_type": by_type,
            "by_source": by_source,
            "organisms": int((await session.execute(select(func.count(Organism.id)))).scalar_one()),
            "organism_groups": by_group,
            "publications": int(
                (await session.execute(select(func.count(Publication.id)))).scalar_one()
            ),
            "unique_pmids": pmid_count,
            "sequence_links": int(
                (await session.execute(select(func.count(SequenceReference.sequence_id)))).scalar_one()
            ),
            "genomes": int(
                (await session.execute(select(func.count(GenomeRecord.id)))).scalar_one()
            ),
            "duplicate_keys": len(dup_rows),
        }


def _print_snapshot(label: str, data: dict[str, Any]) -> None:
    print("\n" + "=" * 64)
    print(label)
    print("=" * 64)
    print(f"  sequences      {data['sequences']}")
    for key, value in sorted((data.get("by_type") or {}).items()):
        print(f"    {key:<12} {value}")
    print(f"  genomes        {data['genomes']}")
    print(f"  organisms      {data['organisms']}")
    print(f"  publications   {data['publications']}")
    print(f"  unique PMIDs   {data.get('unique_pmids', '—')}")
    print(f"  seq-pub links  {data['sequence_links']}")
    print(f"  duplicate keys {data['duplicate_keys']}")
    print("  sources:")
    for key, value in sorted((data.get("by_source") or {}).items()):
        print(f"    {key:<16} {value}")


def _max_length_for(seq_type: str | None, global_cap: int | None) -> int | None:
    category_cap = DEFAULT_MAX_LENGTHS.get(seq_type or "", None)
    if global_cap is None:
        return category_cap
    if category_cap is None:
        return global_cap
    return min(category_cap, global_cap)


def _filter_records(
    records: list[ParsedSequence],
    *,
    checkpoint: dict[str, Any],
    additional: int,
    global_cap: int | None,
) -> tuple[list[ParsedSequence], int, int]:
    """Drop overlong records and over-represented species. Never truncate residues."""
    kept: list[ParsedSequence] = []
    skipped_long = 0
    skipped_dom = 0
    counts = tax_counts(checkpoint)
    for ps in records:
        cap = _max_length_for(ps.seq_type, global_cap)
        length = ps.effective_length()
        if cap is not None and length > cap:
            skipped_long += 1
            continue
        tax_id = ps.organism.tax_id if ps.organism else None
        if (
            isinstance(tax_id, int)
            and tax_id > 0
            and species_over_new_cap(tax_id, counts, additional)
        ):
            skipped_dom += 1
            continue
        kept.append(ps)
        if isinstance(tax_id, int) and tax_id > 0:
            counts[tax_id] = counts.get(tax_id, 0) + 1
    return kept, skipped_long, skipped_dom


async def _known_accessions(accessions: list[str]) -> set[str]:
    unique = [a for a in dict.fromkeys(accessions) if a]
    if not unique:
        return set()
    async with get_sessionmaker()() as session:
        rows = (
            await session.execute(
                select(Sequence.accession).where(Sequence.accession.in_(unique))
            )
        ).scalars()
        return set(rows.all())


def _note_new_taxa(checkpoint: dict[str, Any], records: list[ParsedSequence], known: set[str]) -> None:
    for ps in records:
        if ps.accession in known:
            continue
        tax_id = ps.organism.tax_id if ps.organism else None
        if isinstance(tax_id, int) and tax_id > 0:
            add_new_tax(checkpoint, tax_id, 1)


def _bump_category(checkpoint: dict[str, Any], category: str | None, created: int) -> None:
    if not category or created <= 0:
        return
    bucket = checkpoint.setdefault("new_by_category", {})
    bucket[category] = int(bucket.get(category) or 0) + created


def _should_skip_sequence_job(
    job: dict[str, Any],
    stats: dict[str, Any],
    checkpoint: dict[str, Any],
    additional: int,
    ceiling: int,
) -> str | None:
    if job.get("kind") == "genomes":
        return None
    total = int(stats["sequences"])
    hard_stop = ceiling + max(200, additional // 20)
    if total >= hard_stop:
        return f"hard stop at {total} (ceiling {ceiling})"
    cat = str(job.get("category") or "")
    share = CATEGORY_SHARES.get(cat)
    if share is None or total < ceiling:
        return None
    new_cat = int((checkpoint.get("new_by_category") or {}).get(cat) or 0)
    cat_target = int(additional * share)
    if new_cat >= cat_target:
        return f"{cat} share filled ({new_cat}>={cat_target}) and total {total}>={ceiling}"
    return None


async def _retry(factory: Callable[[], Awaitable[ImportReport]], *, attempts: int = 3) -> ImportReport:
    last: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return await factory()
        except Exception as exc:  # noqa: BLE001 — transient upstream failures
            last = exc
            message = str(exc).lower()
            if "not found" in message or "404" in message:
                raise
            wait = min(2 ** attempt, 30)
            print(f"      retry {attempt}/{attempts} after error: {exc} (sleep {wait}s)")
            await asyncio.sleep(wait)
    raise last  # type: ignore[misc]


def _apply_crispr_defaults(records: list[ParsedSequence], job: dict[str, Any]) -> None:
    evidence = job.get("evidence_type") or CrisprEvidenceType.NATURAL_CRISPR_ELEMENT.value
    if job.get("seq_type") != "crispr" and job.get("category") != "crispr":
        return
    for ps in records:
        if ps.seq_type == "crispr" and not ps.evidence_type:
            ps.evidence_type = evidence


async def _fetch_job_records(job: dict[str, Any], batch_size: int) -> list[ParsedSequence]:
    kind = job["kind"]
    if kind == "ncbi":
        return await ncbi.fetch_records(
            term=job["term"],
            limit=int(job["limit"]),
            seq_type=job.get("seq_type"),
            db=job.get("db", "nuccore"),
        )
    if kind == "uniprot":
        return await uniprot.fetch_records(query=job["query"], limit=int(job["limit"]))
    if kind == "pdb":
        from app.pipeline.fetchers.pdb import fetch_records as pdb_fetch

        return await pdb_fetch(job["ids"])
    if kind == "rfam":
        return []
    return []


async def _run_job(
    job: dict[str, Any],
    *,
    checkpoint: dict[str, Any],
    additional: int,
    batch_size: int,
    dry_run: bool,
    global_cap: int | None,
) -> ImportReport:
    kind = job["kind"]
    if kind == "genomes":
        if dry_run:
            print(f"      dry-run skip persist genomes taxon={job.get('taxon')}")
            return ImportReport()
        return await datasets.ingest(taxon=job["taxon"], limit=int(job["limit"]))
    if kind == "rfam":
        if dry_run:
            print(f"      dry-run skip persist rfam {job.get('family')}")
            return ImportReport()
        return await rfam.ingest_family(job["family"], limit=int(job["limit"]), batch_size=batch_size)
    if kind == "computational_ngg":
        return await run_computational_ngg(
            checkpoint,
            limit=int(job.get("limit") or 80),
            dry_run=dry_run,
            batch_size=batch_size,
            additional=additional,
        )
    records = await _fetch_job_records(job, batch_size)

    _apply_crispr_defaults(records, job)
    kept, n_long, n_dom = _filter_records(
        records, checkpoint=checkpoint, additional=additional, global_cap=global_cap
    )
    report = ImportReport(total=len(records), skipped=n_long + n_dom)
    if n_long:
        report.errors.append(f"{n_long} over-length record(s) skipped (not truncated)")
    if n_dom:
        report.errors.append(f"{n_dom} record(s) skipped to diversify taxa")
    if dry_run:
        checkpoint.setdefault("candidates", []).extend(
            {
                "job": job["id"],
                "source": ps.source_key,
                "accession": ps.accession,
                "version": ps.version,
                "category": job.get("category") or ps.seq_type,
                "tax_id": ps.organism.tax_id if ps.organism else None,
                "organism": ps.organism.scientific_name if ps.organism else None,
                "length": ps.effective_length(),
                "reason": job.get("reason"),
            }
            for ps in kept[:200]
        )
        report.skipped += len(kept)
        return report
    if not kept:
        return report
    known = await _known_accessions([ps.accession for ps in kept])
    imported = await import_with_run(
        kept,
        source_key=str(job.get("kind") or "expansion"),
        kind="expansion_job",
        params={"id": job["id"], "limit": job.get("limit")},
        batch_size=batch_size,
    )
    _merge(report, imported)
    _note_new_taxa(checkpoint, kept, known)
    _bump_category(checkpoint, job.get("category"), imported.created)
    checkpoint["inserted"] = int(checkpoint.get("inserted") or 0) + imported.created
    checkpoint["updated"] = int(checkpoint.get("updated") or 0) + imported.updated
    checkpoint["skipped"] = int(checkpoint.get("skipped") or 0) + imported.skipped + n_long + n_dom
    return report


async def run_computational_ngg(
    checkpoint: dict[str, Any],
    *,
    limit: int,
    dry_run: bool,
    batch_size: int,
    additional: int,
) -> ImportReport:
    """Cas9 NGG sites copied from allowlisted authentic DNA already in BioWiki."""
    async with get_sessionmaker()() as session:
        rows = list(
            (
                await session.execute(
                    select(Sequence)
                    .join(Organism)
                    .where(
                        Sequence.seq_type == SequenceType.DNA,
                        Organism.tax_id.in_(list(COMPUTATIONAL_TAX_IDS)),
                        Sequence.length.between(200, 20_000),
                        Sequence.residues.is_not(None),
                    )
                    .options(selectinload(Sequence.organism), selectinload(Sequence.source))
                    .order_by(Organism.tax_id, Sequence.length.desc())
                )
            )
            .scalars()
            .unique()
            .all()
        )
    per_taxon: dict[int, int] = {}
    parsed: list[ParsedSequence] = []
    for seq in rows:
        org = seq.organism
        if org is None or org.tax_id not in COMPUTATIONAL_TAX_IDS:
            continue
        if per_taxon.get(org.tax_id, 0) >= 2:
            continue
        if not seq.residues:
            continue
        sites = find_cas9_ngg_sites(seq.residues, max_sites=4)
        if not sites:
            continue
        per_taxon[org.tax_id] = per_taxon.get(org.tax_id, 0) + 1
        for site in sites:
            if len(parsed) >= limit:
                break
            start_1 = site.start + 1
            accession = f"NGG.{seq.accession}.{start_1}.{site.strand}"[:64]
            parsed.append(
                ParsedSequence(
                    seq_type="crispr",
                    accession=accession,
                    version="1",
                    name=(
                        f"Computational Cas9 NGG site {start_1}-{site.end} "
                        f"({site.strand}) on {seq.accession}"
                    ),
                    organism=ParsedOrganism(
                        scientific_name=org.scientific_name,
                        tax_id=org.tax_id,
                        common_name=org.common_name,
                        group=org.group.value if org.group is not None else None,
                        lineage=list(org.lineage or []),
                    ),
                    source_key=COMPUTATIONAL_SOURCE_KEY,
                    source_name="BioWiki computational Cas9 NGG scan",
                    molecule="dna",
                    residues=site.spacer,
                    length=len(site.spacer),
                    cas_system="cas9",
                    evidence_type=CrisprEvidenceType.COMPUTATIONAL_TARGET.value,
                    pam="NGG",
                    target_gene=seq.gene_name,
                    genomic_target=f"{seq.accession}:{start_1}-{site.end}:{site.strand}",
                    target_source_accession=seq.accession,
                    target_tax_id=org.tax_id,
                    method=COMPUTATIONAL_METHOD,
                    on_target_score=None,
                    off_target_score=None,
                    source_url=seq.source_url,
                    description=(
                        "Predicted Cas9 NGG spacer copied from an authentic stored DNA "
                        "record. Not experimental. No living organism was edited."
                    ),
                    annotations={
                        "target_accession": seq.accession,
                        "target_version": seq.version,
                        "pam_rule": "NGG",
                        "spacer_len": 20,
                    },
                )
            )
        if len(parsed) >= limit:
            break

    report = ImportReport(total=len(parsed))
    if dry_run:
        report.skipped = len(parsed)
        return report
    if not parsed:
        return report
    imported = await import_with_run(
        parsed,
        source_key=COMPUTATIONAL_SOURCE_KEY,
        kind="computational_ngg",
        params={"method": COMPUTATIONAL_METHOD, "limit": limit},
        batch_size=batch_size,
    )
    _merge(report, imported)
    _bump_category(checkpoint, "crispr", imported.created)
    return report


async def refresh_and_integrity() -> dict[str, Any]:
    from app.services import sync_service

    async with get_sessionmaker()() as session:
        refreshed = await sync_service.refresh_counts(session)
        integrity = await sync_service.check_integrity(session)
    dumped = integrity.model_dump(by_alias=True, mode="json")
    if not dumped.get("ok"):
        raise RuntimeError(f"integrity check failed: {json.dumps(dumped, default=str)[:2000]}")
    return {"refreshed": refreshed, "integrity": dumped}


def _mark_failed(checkpoint: dict[str, Any], path: Path, job_id: str, error: str) -> None:
    checkpoint.setdefault("failed", {})[job_id] = error
    checkpoint["temporary_failure"] = int(checkpoint.get("temporary_failure") or 0) + 1
    save_checkpoint(path, checkpoint)


def _mark_completed(
    checkpoint: dict[str, Any], path: Path, job_id: str, report: ImportReport
) -> None:
    completed = set(checkpoint.get("completed") or [])
    completed.add(job_id)
    checkpoint["completed"] = sorted(completed)
    failed = checkpoint.setdefault("failed", {})
    if job_id in failed:
        history = checkpoint.setdefault("failed_history", {})
        history[job_id] = failed.pop(job_id)
    checkpoint.setdefault("reports", []).append({"id": job_id, **report.as_dict()})
    save_checkpoint(path, checkpoint)


async def run_sequence_jobs(
    checkpoint: dict[str, Any],
    path: Path,
    jobs: list[dict[str, Any]],
    *,
    additional: int,
    ceiling: int,
    batch_size: int,
    dry_run: bool,
    global_cap: int | None,
) -> ImportReport:
    combined = ImportReport()
    completed = set(checkpoint.get("completed") or [])
    for index, job in enumerate(jobs, start=1):
        job_id = job["id"]
        checkpoint["job_id"] = job_id
        checkpoint["source"] = job.get("kind")
        checkpoint["category"] = job.get("category")
        checkpoint["batch_number"] = index
        checkpoint["candidate_position"] = index
        stats = await snapshot()
        skip_reason = _should_skip_sequence_job(job, stats, checkpoint, additional, ceiling)
        if skip_reason:
            print(f"  skip {job_id}: {skip_reason}")
            if job_id not in completed:
                completed.add(job_id)
                checkpoint["completed"] = sorted(completed)
                save_checkpoint(path, checkpoint)
            continue
        if job_id in completed:
            print(f"  skip {job_id}: already in checkpoint")
            continue
        failed_map = checkpoint.get("failed") or {}
        if job_id in failed_map:
            print(f"  retry {job_id}: previously failed ({str(failed_map[job_id])[:80]})")
        print(f"\n[{job_id}] {job['kind']} limit={job.get('limit', '-')}")
        try:
            report = await _retry(
                lambda j=job: _run_job(
                    j,
                    checkpoint=checkpoint,
                    additional=additional,
                    batch_size=batch_size,
                    dry_run=dry_run,
                    global_cap=global_cap,
                )
            )
        except Exception as exc:  # noqa: BLE001
            _mark_failed(checkpoint, path, job_id, str(exc))
            print(f"      FAILED {job_id}: {exc}")
            continue
        _show(job_id, report)
        if _source_job_failed(report) or report.failed > 0:
            _mark_failed(
                checkpoint,
                path,
                job_id,
                "; ".join(report.errors[:3]) or "source unavailable",
            )
            print(f"      FAILED {job_id}: not marked completed ({report.failed} failed)")
            continue
        _merge(combined, report)
        checkpoint["last_stats"] = await snapshot()
        _mark_completed(checkpoint, path, job_id, report)
        completed = set(checkpoint.get("completed") or [])
        if (not dry_run) and (report.created or report.updated) and index % 15 == 0:
            try:
                await refresh_and_integrity()
            except RuntimeError as exc:
                print(f"      STOP integrity failed after {job_id}: {exc}")
                raise
    return combined


async def run_pubmed(
    checkpoint: dict[str, Any],
    path: Path,
    *,
    publication_target: int,
    dry_run: bool,
) -> ImportReport:
    combined = ImportReport()
    completed = set(checkpoint.get("completed") or [])

    elink_id = "pubmed-elink-all"
    if elink_id not in completed:
        async with get_sessionmaker()() as session:
            accessions = list(
                (
                    await session.execute(
                        select(Sequence.accession)
                        .join(DataSource, Sequence.source_id == DataSource.id)
                        .where(DataSource.key.in_(["ncbi_genbank", "ncbi_refseq"]))
                    )
                )
                .scalars()
                .all()
            )
        print(f"\n[{elink_id}] {len(accessions)} NCBI accession(s)")
        if dry_run:
            print("      dry-run skip PubMed ELink persist")
        else:
            try:
                report = await _retry(
                    lambda: pubmed.ingest_elinks(accessions, dbfrom="nuccore", max_pmids=12000)
                )
                _show(elink_id, report)
                _merge(combined, report)
            except Exception as exc:  # noqa: BLE001
                checkpoint.setdefault("failed", {})[elink_id] = str(exc)
                print(f"      FAILED {elink_id}: {exc}")
        completed.add(elink_id)
        checkpoint["completed"] = sorted(completed)
        checkpoint["last_stats"] = await snapshot()
        save_checkpoint(path, checkpoint)

    for search_id, term, limit in PUBMED_SEARCHES:
        stats = await snapshot()
        remaining = publication_remaining(stats["publications"], publication_target)
        if remaining <= 0:
            print(f"  skip {search_id}: publication total target reached ({stats['publications']})")
            break
        if search_id in completed:
            print(f"  skip {search_id}: already in checkpoint")
            continue
        page_limit = min(limit, max(remaining, 50), 400)
        print(f"\n[{search_id}] PubMed search limit={page_limit} remaining={remaining}")
        if dry_run:
            completed.add(search_id)
            checkpoint["completed"] = sorted(completed)
            save_checkpoint(path, checkpoint)
            continue
        retstart = 0
        pages = 0
        try:
            while remaining > 0 and pages < 8:
                chunk = min(page_limit, remaining + 25, 400)
                report = await _retry(
                    lambda t=term, n=chunk, s=retstart: pubmed.ingest_search(
                        t, limit=n, retstart=s
                    )
                )
                _show(f"{search_id}-p{pages + 1}", report)
                _merge(combined, report)
                pages += 1
                retstart += chunk
                if report.created == 0:
                    break
                stats = await snapshot()
                remaining = publication_remaining(stats["publications"], publication_target)
        except Exception as exc:  # noqa: BLE001
            checkpoint.setdefault("failed", {})[search_id] = str(exc)
            save_checkpoint(path, checkpoint)
            print(f"      FAILED {search_id}: {exc}")
            continue
        completed.add(search_id)
        checkpoint["completed"] = sorted(completed)
        checkpoint["last_stats"] = await snapshot()
        save_checkpoint(path, checkpoint)

    backfill_id = "pubmed-backfill"
    if backfill_id not in completed and not dry_run:
        print(f"\n[{backfill_id}]")
        async with get_sessionmaker()() as session:
            pmids = list(
                (
                    await session.execute(
                        select(Publication.pubmed_id)
                        .where(
                            Publication.pubmed_id.is_not(None),
                            (Publication.journal.is_(None)) | (Publication.abstract.is_(None)),
                        )
                        .order_by(Publication.pubmed_id)
                        .limit(800)
                    )
                )
                .scalars()
                .all()
            )
        if pmids:
            try:
                report = await _retry(lambda: pubmed.ingest_pmids(list(pmids)))
                _show(backfill_id, report)
                _merge(combined, report)
            except Exception as exc:  # noqa: BLE001
                checkpoint.setdefault("failed", {})[backfill_id] = str(exc)
                print(f"      FAILED {backfill_id}: {exc}")
        completed.add(backfill_id)
        checkpoint["completed"] = sorted(completed)
        checkpoint["last_stats"] = await snapshot()
        save_checkpoint(path, checkpoint)
    return combined


async def run_expansion(
    *,
    additional_sequences: int,
    publication_target: int,
    batch_size: int = 200,
    resume: bool = True,
    dry_run: bool = False,
    validate_only: bool = False,
    sources: set[str] | None = None,
    categories: set[str] | None = None,
    diversity_plan: bool = False,
    max_record_length: int | None = None,
    report_path: Path | None = None,
    sequences_only: bool = False,
    pubmed_only: bool = False,
    checkpoint_path: Path | None = None,
) -> dict[str, Any]:
    path = checkpoint_path or (
        Path(__file__).resolve().parents[3] / "data" / "expansion_checkpoint.json"
    )
    jobs = build_sequence_jobs(
        additional_sequences, categories=categories, sources=sources
    )
    plan = summarize_plan(jobs)
    print(json.dumps(plan, indent=2))
    if diversity_plan:
        for job in jobs:
            print(
                f"  {job['id']:<42} {job['kind']:<18} "
                f"cat={job.get('category')} limit={job.get('limit', '-')}"
            )
        return {"plan": plan, "jobs": jobs}

    checkpoint = load_checkpoint(path) if resume else default_checkpoint()

    before = await snapshot()
    if checkpoint.get("before") is None:
        checkpoint["before"] = before
    checkpoint["config"] = {
        "additional_sequences": additional_sequences,
        "publication_target": publication_target,
        "batch_size": batch_size,
        "dry_run": dry_run,
        "max_record_length": max_record_length,
        "sequence_semantics": "additional",
        "publication_semantics": "total",
    }
    save_checkpoint(path, checkpoint)
    _print_snapshot("DATASET BEFORE", before)

    ceiling = sequence_ceiling(int(before["sequences"]), additional_sequences)
    print(
        f"\nTargets: sequences {before['sequences']} + {additional_sequences} "
        f"-> ceiling {ceiling}; publications TOTAL {publication_target} "
        f"(now {before['publications']})"
    )

    if validate_only:
        sync_info = await refresh_and_integrity()
        print("integrity ok:", sync_info["integrity"].get("ok"))
        return {"before": before, "integrity": sync_info["integrity"], "plan": plan}

    seq_report = ImportReport()
    pub_report = ImportReport()
    if not pubmed_only:
        print("\n--- sequence expansion ---")
        _merge(
            seq_report,
            await run_sequence_jobs(
                checkpoint,
                path,
                jobs,
                additional=additional_sequences,
                ceiling=ceiling,
                batch_size=batch_size,
                dry_run=dry_run,
                global_cap=max_record_length,
            ),
        )
    if not sequences_only:
        print("\n--- PubMed expansion (total target) ---")
        _merge(
            pub_report,
            await run_pubmed(
                checkpoint,
                path,
                publication_target=publication_target,
                dry_run=dry_run,
            ),
        )

    print("\n--- refresh counters / integrity ---")
    sync_info = await refresh_and_integrity()
    print(json.dumps(sync_info["refreshed"], indent=2))
    print("integrity ok:", sync_info["integrity"].get("ok"))

    after = await snapshot()
    checkpoint["after"] = after
    checkpoint["sequence_report"] = seq_report.as_dict()
    checkpoint["publication_report"] = pub_report.as_dict()
    save_checkpoint(path, checkpoint)
    _print_snapshot("DATASET AFTER", after)

    before_saved = checkpoint.get("before") or before
    summary = {
        "before": before_saved,
        "after": after,
        "sequences_delta": after["sequences"] - before_saved["sequences"],
        "publications_delta": after["publications"] - before_saved["publications"],
        "ceiling": ceiling,
        "publication_target": publication_target,
        "integrity": sync_info["integrity"],
        "plan": plan,
        "dry_run": dry_run,
        "checkpoint": str(path),
        "finished_at": datetime.now(timezone.utc).isoformat(),
    }
    print("\n" + "=" * 64)
    print("EXPANSION DELTA")
    print("=" * 64)
    print(
        f"  sequences      {before_saved['sequences']} -> {after['sequences']}  "
        f"(+{summary['sequences_delta']})"
    )
    print(
        f"  publications   {before_saved['publications']} -> {after['publications']}  "
        f"(+{summary['publications_delta']})"
    )
    if report_path:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
        print(f"  report         {report_path}")
    print(f"  checkpoint     {path}")
    return summary
