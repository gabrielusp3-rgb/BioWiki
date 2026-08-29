"""Phase 0 scientific audit of the current catalogue.

Read-only against PostgreSQL. External 429/timeout/5xx → TEMPORARILY_UNVERIFIED.
Resumable via ``backend/.audit/phase0.json``. Never deletes rows.

Run from ``backend/``::

    python -m scripts.phase0_audit
    python -m scripts.phase0_audit --resume
    python -m scripts.phase0_audit --skip-external
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.stdio import configure_utf8_stdio

configure_utf8_stdio()

from sqlalchemy import func, select, text

from app.database.session import get_sessionmaker
from app.models.enums import SequenceType
from app.models.genome import GenomeRecord
from app.models.organism import Organism
from app.models.publication import Publication, SequenceReference
from app.models.sequence import Sequence
from app.models.source import DataSource
from app.pipeline.fetchers.base import chunked
from app.pipeline.phase0.checkpoint import (
    load_checkpoint,
    mark,
    needs_retry,
    record_key,
    save_checkpoint,
)
from app.pipeline.phase0.errors import classify_external_error
from app.pipeline.phase0.names import classify_organism_taxonomy
from app.pipeline.taxonomy import group_from_taxonomy, index_taxonomy_for_requested
from app.pipeline.validation import pubmed_id_is_valid
from app.services import sync_service
from app.services.connectors.errors import ConnectorError, ConnectorNotFound
from app.services.connectors.ncbi import NCBIConnector
from app.services.connectors.pdb import PDBConnector
from app.services.connectors.rfam import RfamConnector
from app.services.connectors.uniprot import UniProtConnector

CHECKPOINT_PATH = Path(__file__).resolve().parent.parent / ".audit" / "phase0.json"
BASELINE_PATH = Path(__file__).resolve().parent.parent / ".audit" / "pre-10k-verified-baseline.json"

_NCBI_BATCH = 200
_UNIPROT_BATCH = 20
_TAXONOMY_BATCH = 40
_PUBMED_BATCH = 200
_TRANSCRIPT_PREFIXES = ("NM_", "NR_", "XM_", "XR_")
_UNIPROT_ACC = re.compile(
    r"^[OPQ][0-9][A-Z0-9]{3}[0-9]$|^[A-NR-Z][0-9](?:[A-Z][A-Z0-9]{2}[0-9]){1,2}$"
)
_PDB_ENTITY = re.compile(r"^[0-9][A-Z0-9]{3}_")
_REFSEQ_PROTEIN = ("NP_", "XP_", "YP_", "WP_")


def _ncbi_status(rec: dict[str, Any]) -> str:
    extra = str(rec.get("extra") or "").lower()
    if rec.get("replacedby") or "replaced" in extra or str(rec.get("status") or "").lower() in {
        "suppressed",
        "replaced",
        "withdrawn",
    }:
        return "SUPERSEDED"
    inactive = rec.get("inactiveReason") or rec.get("entryType")
    if isinstance(inactive, str) and "inactive" in inactive.lower():
        return "SUPERSEDED"
    return "VERIFIED"


def _index_esummary(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result = payload.get("result") or {}
    out: dict[str, dict[str, Any]] = {}
    for uid in result.get("uids") or []:
        rec = result.get(str(uid)) or result.get(uid) or {}
        if not isinstance(rec, dict):
            continue
        rec = dict(rec)
        rec["_status"] = _ncbi_status(rec)
        accver = str(rec.get("accessionversion") or rec.get("caption") or rec.get("uid") or uid)
        bare = accver.split(".")[0]
        out[bare] = rec
        out[accver] = rec
        out[str(uid)] = rec
        caption = rec.get("caption")
        if caption:
            out[str(caption)] = rec
    return out


async def _esummary_history(conn: NCBIConnector, db: str, ids: list[str]) -> dict[str, dict[str, Any]]:
    try:
        webenv, query_key = await conn.epost(db, ids)
        payload = await conn.esummary(db, webenv=webenv, query_key=query_key, retmax=len(ids) + 10)
        return _index_esummary(payload)
    except ConnectorError as exc:
        if classify_external_error(exc) == "TEMPORARILY_UNVERIFIED":
            raise
        payload = await conn.esummary(db, ids)
        return _index_esummary(payload)


def _compare_nucleotide(
    *,
    seq_type: str,
    stored_len: int | None,
    stored_tax: int | None,
    rec: dict[str, Any],
) -> str:
    status = rec.get("_status") or "VERIFIED"
    if status == "SUPERSEDED":
        return "SUPERSEDED"
    slen = rec.get("slen")
    if stored_len is not None and slen is not None and int(stored_len) != int(slen):
        return "MISMATCH"
    taxid = rec.get("taxid")
    if stored_tax and taxid is not None and int(stored_tax) != int(taxid):
        return "MISMATCH"
    mol = str(rec.get("moltype") or rec.get("biomol") or "").lower()
    acc = str(rec.get("caption") or rec.get("accessionversion") or "")
    if seq_type == "dna" and "rna" in mol and acc.split(".")[0].startswith(_TRANSCRIPT_PREFIXES):
        return "MISMATCH"
    if seq_type == "rna" and mol in {"dna", "genomic"} and "rna" not in mol:
        return "MISMATCH"
    return "VERIFIED"


def _route_sequence(accession: str, source_key: str, seq_type: str) -> str:
    acc = accession.strip()
    if acc.startswith("RF"):
        return "rfam"
    if _PDB_ENTITY.match(acc):
        return "pdb"
    if acc.startswith(_REFSEQ_PROTEIN):
        return "ncbi_protein"
    if source_key in {"uniprot", "uniprotkb"} or _UNIPROT_ACC.match(acc):
        return "uniprot"
    return "nuccore"


async def snapshot(session) -> dict[str, Any]:
    type_rows = (
        await session.execute(
            select(Sequence.seq_type, func.count(), func.coalesce(func.sum(Sequence.length), 0))
            .group_by(Sequence.seq_type)
        )
    ).all()
    by_type = {row[0].value if hasattr(row[0], "value") else str(row[0]): (int(row[1]), int(row[2])) for row in type_rows}
    sources = dict(
        (
            await session.execute(
                select(DataSource.name, func.count(Sequence.id))
                .join(Sequence, Sequence.source_id == DataSource.id)
                .group_by(DataSource.name)
            )
        ).all()
    )
    organisms = list((await session.execute(select(Organism))).scalars().all())
    rank_counts = Counter((o.rank or "unknown") for o in organisms)
    unique_tax = len({int(o.tax_id) for o in organisms})
    pubs = int((await session.execute(select(func.count()).select_from(Publication))).scalar_one())
    pmids = int(
        (
            await session.execute(
                select(func.count()).where(Publication.pubmed_id.is_not(None))
            )
        ).scalar_one()
    )
    linked = int(
        (
            await session.execute(
                select(func.count(func.distinct(SequenceReference.publication_id)))
            )
        ).scalar_one()
    )
    genomes = int((await session.execute(select(func.count()).select_from(GenomeRecord))).scalar_one())
    checksum_clusters = int(
        (
            await session.execute(
                select(func.count())
                .select_from(
                    select(Sequence.checksum)
                    .where(Sequence.checksum.is_not(None), Sequence.checksum != "")
                    .group_by(Sequence.checksum)
                    .having(func.count() > 1)
                    .subquery()
                )
            )
        ).scalar_one()
    )
    db_size = None
    try:
        db_size = int((await session.execute(text("SELECT pg_database_size(current_database())"))).scalar_one())
    except Exception:
        db_size = None

    def _n(key: str) -> int:
        return by_type.get(key, (0, 0))[0]

    def _r(key: str) -> int:
        return by_type.get(key, (0, 0))[1]

    total_seq = sum(n for n, _ in by_type.values())
    total_res = sum(r for _, r in by_type.values())
    return {
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "sequences_total": total_seq,
        "dna": _n("dna"),
        "rna": _n("rna"),
        "protein": _n("protein"),
        "peptide": _n("peptide"),
        "crispr": _n("crispr"),
        "virus": _n("virus"),
        "genome_sequence_rows": _n("genome"),
        "genome_assemblies": genomes,
        "organisms": len(organisms),
        "unique_tax_ids": unique_tax,
        "publications": pubs,
        "unique_pmids": pmids,
        "directly_linked_publications": linked,
        "residue_count": total_res,
        "checksum_clusters": checksum_clusters,
        "ranks": dict(rank_counts),
        "data_sources": {str(k): int(v) for k, v in sources.items()},
        "database_bytes": db_size,
        "species": rank_counts.get("species", 0),
        "genera": rank_counts.get("genus", 0),
        "families": rank_counts.get("family", 0),
    }


async def _verify_ncbi_accessions(
    *,
    conn: NCBIConnector,
    db: str,
    rows: list[tuple[str, str, str | None, str, int | None, int | None]],
    checkpoint: dict[str, Any],
    path: Path,
    source_label: str,
) -> None:
    pending = []
    for source_name, accession, version, seq_type, length, tax_id in rows:
        key = record_key(source_name, accession, version)
        if not needs_retry(checkpoint["records"].get(key)):
            continue
        pending.append((key, accession, seq_type, length, tax_id, source_name, version))
    for batch_i, group in enumerate(chunked(pending, _NCBI_BATCH), start=1):
        ids = [item[1] for item in group]
        print(f"  {source_label} batch {batch_i} n={len(ids)}", flush=True)
        checkpoint["last_completed_position"] = {"source": source_label, "batch": batch_i}
        try:
            indexed = await _esummary_history(conn, db, ids)
        except Exception as exc:  # noqa: BLE001
            status = classify_external_error(exc)
            for key, accession, *_rest in group:
                mark(checkpoint["records"], key, status=status, accession=accession, error=str(exc)[:300])
            save_checkpoint(path, checkpoint)
            continue
        for key, accession, seq_type, length, tax_id, source_name, version in group:
            rec = indexed.get(accession) or indexed.get(accession.split(".")[0])
            if rec is None:
                mark(
                    checkpoint["records"],
                    key,
                    status="NOT_FOUND",
                    accession=accession,
                    note="esummary returned no uid",
                )
                continue
            status = _compare_nucleotide(
                seq_type=seq_type, stored_len=length, stored_tax=tax_id, rec=rec
            )
            mark(
                checkpoint["records"],
                key,
                status=status,
                accession=accession,
                ncbi_slen=rec.get("slen"),
                ncbi_taxid=rec.get("taxid"),
                ncbi_moltype=rec.get("moltype") or rec.get("biomol"),
                ncbi_accession=rec.get("accessionversion"),
            )
        save_checkpoint(path, checkpoint)


async def _ena_fallback(checkpoint: dict[str, Any], path: Path) -> None:
    from app.services.connectors.ena import ENAConnector

    missing = [
        (key, rec)
        for key, rec in checkpoint["records"].items()
        if rec.get("status") == "NOT_FOUND" and rec.get("accession")
    ]
    if not missing:
        return
    print(f"  ENA fallback n={len(missing)}", flush=True)
    async with ENAConnector() as ena:
        for i, (key, rec) in enumerate(missing, start=1):
            acc = rec["accession"]
            try:
                raw = await ena.fetch_record(acc, fmt="xml")
                if raw.content and acc.lower() in raw.content.lower():
                    mark(checkpoint["records"], key, status="VERIFIED", accession=acc, via="ena")
                else:
                    mark(checkpoint["records"], key, status="MISMATCH", accession=acc, via="ena_empty")
            except ConnectorNotFound:
                mark(checkpoint["records"], key, status="INVALID", accession=acc, via="ncbi_and_ena_absent")
            except Exception as exc:  # noqa: BLE001
                mark(
                    checkpoint["records"],
                    key,
                    status=classify_external_error(exc),
                    accession=acc,
                    error=str(exc)[:300],
                )
            if i % 20 == 0:
                save_checkpoint(path, checkpoint)
    save_checkpoint(path, checkpoint)


async def run_audit(*, resume: bool, skip_external: bool, checkpoint_path: Path) -> dict[str, Any]:
    checkpoint = load_checkpoint(checkpoint_path) if resume else load_checkpoint(checkpoint_path)
    if not resume and checkpoint.get("records"):
        # Keep existing terminal rows unless caller omitted --resume; still retry temps.
        pass
    session_factory = get_sessionmaker()
    async with session_factory() as session:
        snap = await snapshot(session)
        integrity = await sync_service.check_integrity(session)
        sequences = list(
            (
                await session.execute(
                    select(
                        Sequence.accession,
                        Sequence.version,
                        Sequence.seq_type,
                        Sequence.length,
                        Sequence.molecule,
                        DataSource.name,
                        DataSource.key,
                        Organism.tax_id,
                        Organism.scientific_name,
                    )
                    .join(DataSource, Sequence.source_id == DataSource.id)
                    .join(Organism, Sequence.organism_id == Organism.id)
                )
            ).all()
        )
        genomes = list(
            (
                await session.execute(
                    select(
                        GenomeRecord.accession,
                        DataSource.name,
                        Organism.tax_id,
                    )
                    .join(DataSource, GenomeRecord.source_id == DataSource.id)
                    .join(Organism, GenomeRecord.organism_id == Organism.id)
                )
            ).all()
        )
        organisms = list((await session.execute(select(Organism))).scalars().all())
        publications = list((await session.execute(select(Publication))).scalars().all())
        linked_pub_ids = set(
            (
                await session.execute(select(SequenceReference.publication_id).distinct())
            )
            .scalars()
            .all()
        )

    report: dict[str, Any] = {
        "snapshot": snap,
        "integrity": {
            "ok": integrity.ok,
            "checks": [c.model_dump(by_alias=True) for c in integrity.checks],
        },
    }

    nuccore_rows = []
    protein_refseq_rows = []
    uniprot_rows = []
    pdb_rows = []
    rfam_rows = []
    for accession, version, seq_type, length, _mol, source_name, source_key, tax_id, _org_name in sequences:
        st = seq_type.value if hasattr(seq_type, "value") else str(seq_type)
        route = _route_sequence(accession, source_key, st)
        row = (
            source_name,
            accession,
            version,
            st,
            int(length) if length is not None else None,
            int(tax_id) if tax_id else None,
        )
        if route == "rfam":
            rfam_rows.append(row)
        elif route == "pdb":
            pdb_rows.append(row)
        elif route == "ncbi_protein":
            protein_refseq_rows.append(row)
        elif route == "uniprot":
            uniprot_rows.append(row)
        else:
            nuccore_rows.append(row)

    if skip_external:
        save_checkpoint(checkpoint_path, checkpoint)
        report["checkpoint"] = {
            "processed": checkpoint.get("processed"),
            "by_status": checkpoint.get("by_status"),
        }
        report["note"] = "external verification skipped"
        return report

    async with NCBIConnector() as ncbi:
        print(f"NCBI nuccore n={len(nuccore_rows)}", flush=True)
        await _verify_ncbi_accessions(
            conn=ncbi,
            db="nuccore",
            rows=nuccore_rows,
            checkpoint=checkpoint,
            path=checkpoint_path,
            source_label="ncbi_nuccore",
        )
        print(f"NCBI protein n={len(protein_refseq_rows)}", flush=True)
        await _verify_ncbi_accessions(
            conn=ncbi,
            db="protein",
            rows=[
                (s, a, v, t, l, tx)
                for s, a, v, t, l, tx in protein_refseq_rows
            ],
            checkpoint=checkpoint,
            path=checkpoint_path,
            source_label="ncbi_protein",
        )

        print("NCBI Taxonomy organisms", flush=True)
        tax_ids = [int(o.tax_id) for o in organisms]
        lookup: dict[int, dict[str, Any]] = {}
        for batch_i, group in enumerate(chunked([str(t) for t in tax_ids], _TAXONOMY_BATCH), start=1):
            checkpoint["last_completed_position"] = {"source": "ncbi_taxonomy", "batch": batch_i}
            try:
                xml = await ncbi.efetch("taxonomy", list(group), rettype="xml", retmode="xml")
                requested = [int(t) for t in group if str(t).isdigit()]
                lookup.update(index_taxonomy_for_requested(xml, requested))
            except Exception as exc:  # noqa: BLE001
                for t in group:
                    key = str(t)
                    if needs_retry(checkpoint["organisms"].get(key)):
                        mark(
                            checkpoint["organisms"],
                            key,
                            status="TEMPORARILY_UNVERIFIED",
                            error=str(exc)[:300],
                        )
                save_checkpoint(checkpoint_path, checkpoint)
                continue
            save_checkpoint(checkpoint_path, checkpoint)

        for org in organisms:
            key = str(int(org.tax_id))
            doc = lookup.get(int(org.tax_id))
            if not doc:
                if needs_retry(checkpoint["organisms"].get(key)):
                    mark(
                        checkpoint["organisms"],
                        key,
                        status="TEMPORARILY_UNVERIFIED",
                        scientific_name=org.scientific_name,
                        name_status="UNRESOLVED",
                    )
                continue
            classified = classify_organism_taxonomy(
                stored_tax_id=int(org.tax_id),
                stored_name=org.scientific_name,
                ncbi=doc,
            )
            inferred = group_from_taxonomy(lineage=doc.get("lineage"), division=doc.get("division"))
            group_ok = inferred is None or inferred == org.group.value
            name_status = classified["status"]
            audit_status = "VERIFIED"
            if name_status == "UNRESOLVED":
                audit_status = "TEMPORARILY_UNVERIFIED"
            elif not group_ok:
                audit_status = "MISMATCH"
            mark(
                checkpoint["organisms"],
                key,
                status=audit_status,
                name_status=name_status,
                stored_group=org.group.value,
                ncbi_group=inferred,
                canonical_tax_id=classified.get("canonical_tax_id"),
                canonical_name=classified.get("canonical_name"),
                rank=doc.get("rank"),
                lineage=doc.get("lineage"),
            )
        save_checkpoint(checkpoint_path, checkpoint)

        print("NCBI assembly", flush=True)
        pending_genomes = [row for row in genomes if needs_retry(checkpoint["genomes"].get(row[0]))]
        for batch_i, group in enumerate(chunked(pending_genomes, 8), start=1):
            checkpoint["last_completed_position"] = {"source": "ncbi_assembly", "batch": batch_i}
            print(f"  assembly batch {batch_i} n={len(group)}", flush=True)
            for acc, _src, tax_id in group:
                try:
                    page = await ncbi.esearch(
                        "assembly", f'"{acc}"[Assembly Accession]', retmax=5
                    )
                    if not page.hits:
                        page = await ncbi.esearch("assembly", acc, retmax=5)
                    if not page.hits:
                        mark(
                            checkpoint["genomes"],
                            acc,
                            status="TEMPORARILY_UNVERIFIED",
                            note="assembly esearch returned no UID",
                        )
                        continue
                    payload = await ncbi.esummary(
                        "assembly", [hit.identifier for hit in page.hits[:1]]
                    )
                    indexed = _index_esummary(payload)
                    rec = next(iter(indexed.values()), None)
                    if rec is None:
                        mark(
                            checkpoint["genomes"],
                            acc,
                            status="TEMPORARILY_UNVERIFIED",
                            note="assembly esummary empty after esearch hit",
                        )
                    else:
                        mark(
                            checkpoint["genomes"],
                            acc,
                            status=rec.get("_status") or "VERIFIED",
                            ncbi_taxid=rec.get("taxid") or rec.get("taxidlist"),
                            uid=page.hits[0].identifier,
                        )
                except Exception as exc:  # noqa: BLE001
                    mark(
                        checkpoint["genomes"],
                        acc,
                        status=classify_external_error(exc),
                        error=str(exc)[:300],
                    )
            save_checkpoint(checkpoint_path, checkpoint)

        print("PubMed", flush=True)
        pmid_rows = [p for p in publications if p.pubmed_id]
        for batch_i, group in enumerate(chunked(pmid_rows, _PUBMED_BATCH), start=1):
            ids = [str(p.pubmed_id) for p in group]
            checkpoint["last_completed_position"] = {"source": "pubmed", "batch": batch_i}
            retryable = [p for p in group if needs_retry(checkpoint["publications"].get(str(p.pubmed_id)))]
            if not retryable:
                continue
            try:
                payload = await ncbi.esummary("pubmed", [str(p.pubmed_id) for p in retryable])
                indexed = _index_esummary(payload)
            except Exception as exc:  # noqa: BLE001
                for p in retryable:
                    mark(
                        checkpoint["publications"],
                        str(p.pubmed_id),
                        status=classify_external_error(exc),
                        error=str(exc)[:300],
                    )
                save_checkpoint(checkpoint_path, checkpoint)
                continue
            for p in retryable:
                pid = str(p.pubmed_id)
                rec = indexed.get(pid)
                linked = p.id in linked_pub_ids
                valid_pmid = pubmed_id_is_valid(int(p.pubmed_id))
                if not valid_pmid:
                    klass = "INVALID_PMID"
                    status = "INVALID"
                elif rec is None:
                    klass = "INVALID_PMID"
                    status = "INVALID"
                elif linked:
                    klass = "DIRECT_SEQUENCE_REFERENCE"
                    status = "VERIFIED"
                else:
                    klass = "LEGITIMATE_STANDALONE_CATALOGUE_PUBLICATION"
                    status = "VERIFIED"
                mark(
                    checkpoint["publications"],
                    pid,
                    status=status,
                    classification=klass,
                    title=p.title[:180],
                    linked=linked,
                )
            save_checkpoint(checkpoint_path, checkpoint)

        for p in publications:
            if p.pubmed_id:
                continue
            key = str(p.id)
            linked = p.id in linked_pub_ids
            klass = (
                "DIRECT_SEQUENCE_REFERENCE"
                if linked
                else "LEGITIMATE_STANDALONE_CATALOGUE_PUBLICATION"
            )
            mark(
                checkpoint["publications"],
                key,
                status="VERIFIED",
                classification=klass,
                pubmed_id=None,
                linked=linked,
            )
        save_checkpoint(checkpoint_path, checkpoint)

    print(f"UniProt n={len(uniprot_rows)}", flush=True)
    async with UniProtConnector() as uni:
        pending = [
            row
            for row in uniprot_rows
            if needs_retry(checkpoint["records"].get(record_key(row[0], row[1], row[2])))
        ]
        for batch_i, group in enumerate(chunked(pending, _UNIPROT_BATCH), start=1):
            print(f"  uniprot batch {batch_i} n={len(group)}", flush=True)
            checkpoint["last_completed_position"] = {"source": "uniprot", "batch": batch_i}
            accs = [row[1] for row in group]
            try:
                payload = await uni.get_accessions(accs)
                results = payload.get("results") or []
            except Exception as exc:  # noqa: BLE001
                status = classify_external_error(exc)
                for source_name, acc, version, *_rest in group:
                    mark(
                        checkpoint["records"],
                        record_key(source_name, acc, version),
                        status=status,
                        accession=acc,
                        error=str(exc)[:300],
                    )
                save_checkpoint(checkpoint_path, checkpoint)
                continue
            found: dict[str, dict[str, Any]] = {}
            for rec in results:
                primary = rec.get("primaryAccession") or ""
                found[primary] = rec
                for sec in rec.get("secondaryAccessions") or []:
                    found[str(sec)] = rec
            for source_name, acc, version, seq_type, length, tax_id in group:
                key = record_key(source_name, acc, version)
                rec = found.get(acc)
                if rec is None:
                    mark(checkpoint["records"], key, status="NOT_FOUND", accession=acc)
                    continue
                entry_type = str(rec.get("entryType") or "")
                if "inactive" in entry_type.lower():
                    status = "SUPERSEDED"
                else:
                    seq_len = (rec.get("sequence") or {}).get("length")
                    org = rec.get("organism") or {}
                    status = "VERIFIED"
                    if length is not None and seq_len is not None and int(length) != int(seq_len):
                        status = "MISMATCH"
                    if tax_id and org.get("taxonId") and int(tax_id) != int(org["taxonId"]):
                        status = "MISMATCH"
                mark(
                    checkpoint["records"],
                    key,
                    status=status,
                    accession=acc,
                    uniprot_id=rec.get("primaryAccession"),
                    uniprot_length=(rec.get("sequence") or {}).get("length"),
                )
            save_checkpoint(checkpoint_path, checkpoint)

    print(f"PDB n={len(pdb_rows)}", flush=True)
    async with PDBConnector() as pdb:
        for source_name, acc, version, *_rest in pdb_rows:
            key = record_key(source_name, acc, version)
            if not needs_retry(checkpoint["records"].get(key)):
                continue
            pdb_id = acc.split("_")[0]
            try:
                await pdb.get_entry(pdb_id)
                mark(checkpoint["records"], key, status="VERIFIED", accession=acc, pdb_id=pdb_id)
            except ConnectorNotFound:
                mark(checkpoint["records"], key, status="INVALID", accession=acc)
            except Exception as exc:  # noqa: BLE001
                mark(checkpoint["records"], key, status=classify_external_error(exc), accession=acc, error=str(exc)[:300])
        save_checkpoint(checkpoint_path, checkpoint)

    print(f"Rfam n={len(rfam_rows)}", flush=True)
    async with RfamConnector() as rfam:
        for source_name, acc, version, *_rest in rfam_rows:
            key = record_key(source_name, acc, version)
            if not needs_retry(checkpoint["records"].get(key)):
                continue
            try:
                await rfam.family(acc.split(".")[0])
                mark(checkpoint["records"], key, status="VERIFIED", accession=acc)
            except ConnectorNotFound:
                mark(checkpoint["records"], key, status="INVALID", accession=acc)
            except Exception as exc:  # noqa: BLE001
                mark(checkpoint["records"], key, status=classify_external_error(exc), accession=acc, error=str(exc)[:300])
        save_checkpoint(checkpoint_path, checkpoint)

    await _ena_fallback(checkpoint, checkpoint_path)

    org_metrics = _organism_metrics(checkpoint, organisms)
    pub_metrics = _publication_metrics(checkpoint, publications, linked_pub_ids)
    seq_metrics = _sequence_metrics(checkpoint)
    report["organism_metrics"] = org_metrics
    report["publication_metrics"] = pub_metrics
    report["sequence_metrics"] = seq_metrics
    report["checkpoint"] = {
        "path": str(checkpoint_path),
        "processed": checkpoint.get("processed"),
        "by_status": checkpoint.get("by_status"),
        "last_completed_position": checkpoint.get("last_completed_position"),
        "temporary_failures": checkpoint.get("temporary_failures"),
    }
    report["snapshot"] = snap
    BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
    baseline = {
        **snap,
        "sequence_metrics": seq_metrics,
        "organism_metrics": org_metrics,
        "publication_metrics": pub_metrics,
        "integrity_ok": integrity.ok,
        "temporarily_unverified_preserved": True,
    }
    BASELINE_PATH.write_text(json.dumps(baseline, indent=2, default=str), encoding="utf-8")
    save_checkpoint(checkpoint_path, checkpoint)
    return report


def _organism_metrics(checkpoint: dict[str, Any], organisms: list[Organism]) -> dict[str, Any]:
    names = Counter()
    groups_mismatch = 0
    empty_lineage = 0
    unresolved = 0
    for org in organisms:
        if not org.lineage:
            empty_lineage += 1
        entry = checkpoint["organisms"].get(str(int(org.tax_id))) or {}
        names[entry.get("name_status") or "PENDING"] += 1
        if entry.get("status") == "TEMPORARILY_UNVERIFIED":
            unresolved += 1
        if entry.get("status") == "MISMATCH":
            groups_mismatch += 1
    return {
        "total_organisms": len(organisms),
        "validated_tax_ids": names.get("VALID_NAME", 0) + names.get("VALID_SYNONYM", 0) + names.get("UPDATED_CANONICAL_NAME", 0) + names.get("MERGED_TAXID", 0),
        "canonical_names": names.get("VALID_NAME", 0),
        "valid_synonyms": names.get("VALID_SYNONYM", 0),
        "merged_tax_ids": names.get("MERGED_TAXID", 0),
        "updated_canonical_names": names.get("UPDATED_CANONICAL_NAME", 0),
        "empty_lineage": empty_lineage,
        "unresolved_taxonomy": unresolved,
        "group_mismatch": groups_mismatch,
        "name_status": dict(names),
    }


def _publication_metrics(checkpoint: dict[str, Any], publications: list[Publication], linked_ids: set) -> dict[str, Any]:
    classes = Counter()
    statuses = Counter()
    for key, rec in checkpoint["publications"].items():
        classes[rec.get("classification") or "UNCLASSIFIED"] += 1
        statuses[rec.get("status") or "PENDING"] += 1
    return {
        "total_publications": len(publications),
        "directly_linked_publications": len(linked_ids),
        "standalone_legitimate_publications": classes.get("LEGITIMATE_STANDALONE_CATALOGUE_PUBLICATION", 0),
        "contextual_publications": (
            classes.get("ORGANISM_CONTEXT_PUBLICATION", 0)
            + classes.get("GENE_CONTEXT_PUBLICATION", 0)
            + classes.get("PROTEIN_CONTEXT_PUBLICATION", 0)
            + classes.get("CRISPR_CONTEXT_PUBLICATION", 0)
        ),
        "orphaned_import_artifacts": classes.get("ORPHANED_IMPORT_ARTIFACT", 0),
        "invalid_pmids": classes.get("INVALID_PMID", 0),
        "temporarily_unverified_publications": statuses.get("TEMPORARILY_UNVERIFIED", 0),
        "classifications": dict(classes),
    }


def _sequence_metrics(checkpoint: dict[str, Any]) -> dict[str, Any]:
    statuses = Counter(rec.get("status") for rec in checkpoint["records"].values())
    return {
        "total_checked": sum(statuses.values()),
        "verified_externally": statuses.get("VERIFIED", 0),
        "temporarily_unverifiable": statuses.get("TEMPORARILY_UNVERIFIED", 0),
        "superseded": statuses.get("SUPERSEDED", 0),
        "mismatches": statuses.get("MISMATCH", 0),
        "invalid": statuses.get("INVALID", 0),
        "not_found_pending_ena": statuses.get("NOT_FOUND", 0),
        "by_status": dict(statuses),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resume", action="store_true", default=True)
    parser.add_argument("--fresh", action="store_true", help="Ignore existing checkpoint terminal rows.")
    parser.add_argument("--skip-external", action="store_true")
    parser.add_argument("--checkpoint", type=Path, default=CHECKPOINT_PATH)
    args = parser.parse_args()
    path = args.checkpoint
    if args.fresh and path.exists():
        path.unlink()
    report = asyncio.run(
        run_audit(resume=not args.fresh, skip_external=args.skip_external, checkpoint_path=path)
    )
    print(json.dumps({k: report[k] for k in report if k != "integrity"}, indent=2, default=str)[:12000])
    print("integrity_ok", report["integrity"]["ok"])
    print("checkpoint", report.get("checkpoint"))


if __name__ == "__main__":
    main()
