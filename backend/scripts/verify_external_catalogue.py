"""Checkpointed remote verification of the production catalogue.

Read-only against BioWiki. Never prints secrets. Checkpoints live under
``backend/.audit/external_verify/`` (gitignored).

Run:
  python scripts/with_production_env.py python scripts/verify_external_catalogue.py
  python scripts/with_production_env.py python scripts/verify_external_catalogue.py --phase sequences
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import select

from app.database.session import get_sessionmaker
from app.models.enums import CrisprEvidenceType, SequenceType
from app.models.features import CrisprFeature
from app.models.organism import Organism
from app.models.publication import Publication
from app.models.sequence import Sequence
from app.models.source import DataSource
from app.pipeline.fetchers.base import chunked
from app.pipeline.fetchers.ncbi import lookup_fasta_residues, parse_fasta_residues
from app.services.connectors.errors import (
    ConnectorHTTPError,
    ConnectorNotFound,
    ConnectorRateLimited,
    ConnectorTimeout,
    ConnectorUnavailable,
)
from app.services.connectors.pdb import PDBConnector
from app.services.connectors.ncbi import NCBIConnector
from app.services.connectors.uniprot import UniProtConnector

ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = ROOT / ".audit" / "external_verify"
NCBI_CHUNK = 40
PUBMED_CHUNK = 200
TAX_CHUNK = 200
UNIPROT_CHUNK = 50

_NCBI_KEYS = {
    "ncbi",
    "ncbi_genbank",
    "ncbi_refseq",
    "genbank",
    "refseq",
}
_UNIPROT_KEYS = {"uniprot", "uniprotkb"}
_ENA_KEYS = {"ena"}
_PDB_KEYS = {"pdb", "rcsb"}
_ENSEMBL_KEYS = {"ensembl"}
_RFAM_KEYS = {"rfam"}
_COMPUTATIONAL_KEYS = {"biowiki_computational"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha(residues: str) -> str:
    return hashlib.sha256(residues.encode("ascii", "ignore")).hexdigest()


def _norm_nt(residues: str) -> str:
    return "".join(ch for ch in residues.upper() if not ch.isspace())


def _load_done(path: Path) -> set[str]:
    done: set[str] = set()
    if not path.exists():
        return done
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            key = row.get("id")
            if key:
                done.add(str(key))
    return done


def _append(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def _summarize(path: Path, field: str = "status") -> dict[str, int]:
    counts: Counter[str] = Counter()
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            counts[str(row.get(field) or "unknown")] += 1
            counts["_total"] += 1
    return dict(counts)


def _ids_for_ncbi(accession: str, version: str | None) -> str:
    return f"{accession}.{version}" if version else accession


def _compare_residues(stored: str, remote: str) -> str:
    a = _norm_nt(stored)
    b = _norm_nt(remote)
    if a == b:
        return "VERIFIED_EXACT"
    if a.replace("U", "T") == b.replace("U", "T"):
        return "VERIFIED_EXACT"
    if len(a) != len(b):
        return "LENGTH_MISMATCH"
    return "RESIDUE_MISMATCH"


def _transient(exc: BaseException) -> bool:
    return isinstance(
        exc,
        (ConnectorTimeout, ConnectorUnavailable, ConnectorRateLimited, TimeoutError, OSError),
    )


async def _ncbi_fasta(
    conn: NCBIConnector, db: str, ids: list[str]
) -> tuple[dict[str, str], str | None]:
    try:
        text = await conn.efetch(db, ids, rettype="fasta", retmode="text")
        return parse_fasta_residues(text), None
    except ConnectorNotFound:
        return {}, "CONFIRMED_NOT_FOUND"
    except ConnectorHTTPError as exc:
        if getattr(exc, "status_code", None) == 404:
            return {}, "CONFIRMED_NOT_FOUND"
        return {}, "TEMPORARILY_UNVERIFIED"
    except Exception as exc:
        if _transient(exc):
            return {}, "TEMPORARILY_UNVERIFIED"
        return {}, "TEMPORARILY_UNVERIFIED"


async def _residues_for(ids: list) -> dict:
    if not ids:
        return {}
    async with get_sessionmaker()() as session:
        result = await session.execute(
            select(Sequence.id, Sequence.residues).where(Sequence.id.in_(ids))
        )
        return {row[0]: row[1] or "" for row in result.all()}


def _split_pdb_accession(accession: str) -> tuple[str, str] | None:
    raw = (accession or "").strip().upper()
    if "_" not in raw:
        return None
    pdb_id, entity_id = raw.split("_", 1)
    if not pdb_id or not entity_id:
        return None
    return pdb_id, entity_id


async def _verify_pdb_polymer(pdb: PDBConnector, seq: Any, stored: str) -> dict[str, Any]:
    parsed = _split_pdb_accession(seq.accession)
    base = {
        "id": str(seq.id),
        "accession": seq.accession,
        "version": seq.version,
        "source": getattr(seq, "source_key", "pdb"),
        "type": seq.seq_type.value if hasattr(seq.seq_type, "value") else str(seq.seq_type),
        "provider": "rcsb_pdb",
        "checked_at": _now(),
    }
    if parsed is None:
        return {**base, "status": "TEMPORARILY_UNVERIFIED", "detail": "accession is not PDB_ID_ENTITY"}
    pdb_id, entity_id = parsed
    try:
        await pdb.get_entry(pdb_id)
        entity = await pdb.get_polymer_entity(pdb_id, entity_id)
    except ConnectorNotFound:
        return {**base, "status": "CONFIRMED_MISMATCH", "detail": "PDB entry or polymer entity not found"}
    except Exception as exc:
        status = "TEMPORARILY_UNVERIFIED" if _transient(exc) else "TEMPORARILY_UNVERIFIED"
        return {**base, "status": status, "detail": type(exc).__name__}
    poly = entity.get("entity_poly") or {}
    remote = (poly.get("pdbx_seq_one_letter_code_can") or "").replace("\n", "").strip().upper()
    if not remote:
        return {**base, "status": "METADATA_ONLY_VERIFIED", "detail": "polymer entity exists; canonical residues absent"}
    compared = _compare_residues(stored, remote)
    if compared == "VERIFIED_EXACT":
        return {
            **base,
            "status": "REMOTE_EXACT",
            "queried": f"{pdb_id}_{entity_id}",
            "length_local": len(_norm_nt(stored)),
            "length_remote": len(_norm_nt(remote)),
            "checksum_match": _sha(_norm_nt(stored)) == (getattr(seq, "checksum", None) or ""),
        }
    return {
        **base,
        "status": "CONFIRMED_MISMATCH" if compared in {"RESIDUE_MISMATCH", "LENGTH_MISMATCH"} else compared,
        "detail": compared,
        "queried": f"{pdb_id}_{entity_id}",
        "length_local": len(_norm_nt(stored)),
        "length_remote": len(_norm_nt(remote)),
    }


async def phase_sequences() -> None:
    out = STATE_DIR / "sequences.jsonl"
    done = _load_done(out)
    print("indexing sequences (no residue payload)…", flush=True)
    async with get_sessionmaker()() as session:
        index_rows = (
            await session.execute(
                select(
                    Sequence.id,
                    Sequence.accession,
                    Sequence.version,
                    Sequence.seq_type,
                    Sequence.checksum,
                    DataSource.key,
                    CrisprFeature.evidence_type,
                    CrisprFeature.target_source_accession,
                )
                .join(DataSource, Sequence.source_id == DataSource.id)
                .outerjoin(CrisprFeature, CrisprFeature.sequence_id == Sequence.id)
                .order_by(Sequence.accession)
            )
        ).all()
    print(f"indexed {len(index_rows)} sequences", flush=True)

    class Meta:
        __slots__ = (
            "id",
            "accession",
            "version",
            "seq_type",
            "checksum",
            "source_key",
            "evidence",
            "parent",
        )

        def __init__(self, row):
            self.id = row[0]
            self.accession = row[1]
            self.version = row[2]
            self.seq_type = row[3]
            self.checksum = row[4]
            self.source_key = (row[5] or "").lower()
            self.evidence = row[6]
            self.parent = row[7]

    rows = [Meta(r) for r in index_rows]
    pending_ncbi_nuc: list[Meta] = []
    pending_ncbi_prot: list[Meta] = []
    pending_uniprot: list[Meta] = []
    pending_pdb: list[Meta] = []
    others: list[Meta] = []
    local_accessions = {s.accession for s in rows}
    for seq in rows:
        if str(seq.id) in done:
            continue
        key = seq.source_key
        if key in _COMPUTATIONAL_KEYS or seq.evidence == CrisprEvidenceType.COMPUTATIONAL_TARGET:
            parent = seq.parent
            status = "VERIFIED_DERIVED"
            detail = "computational Cas9 NGG target; parent accession present in catalogue"
            if not parent:
                status = "MANUAL_REVIEW_REQUIRED"
                detail = "computational CRISPR missing parent accession"
            elif parent not in local_accessions:
                status = "MANUAL_REVIEW_REQUIRED"
                detail = "computational parent accession not in catalogue"
            _append(
                out,
                {
                    "id": str(seq.id),
                    "accession": seq.accession,
                    "version": seq.version,
                    "source": key,
                    "type": seq.seq_type.value,
                    "status": status,
                    "detail": detail,
                    "parent": parent,
                    "checked_at": _now(),
                },
            )
            continue
        if key in _UNIPROT_KEYS:
            pending_uniprot.append(seq)
        elif key in _PDB_KEYS:
            pending_pdb.append(seq)
        elif key in _NCBI_KEYS or key in _RFAM_KEYS:
            if seq.seq_type == SequenceType.PROTEIN:
                pending_ncbi_prot.append(seq)
            else:
                pending_ncbi_nuc.append(seq)
        elif key in _ENA_KEYS or key in _ENSEMBL_KEYS:
            others.append(seq)
        else:
            if seq.seq_type == SequenceType.PROTEIN:
                pending_ncbi_prot.append(seq)
            else:
                pending_ncbi_nuc.append(seq)

    async with NCBIConnector() as ncbi:
        for db, group in (("nuccore", pending_ncbi_nuc), ("protein", pending_ncbi_prot)):
            total_chunks = max(1, (len(group) + NCBI_CHUNK - 1) // NCBI_CHUNK)
            for i, chunk in enumerate(chunked(group, NCBI_CHUNK), start=1):
                print(f"ncbi {db} chunk {i}/{total_chunks}", flush=True)
                ids = [_ids_for_ncbi(s.accession, s.version) for s in chunk]
                mapping, batch_status = await _ncbi_fasta(ncbi, db, ids)
                stored_map = await _residues_for([s.id for s in chunk])
                for seq in chunk:
                    ident = _ids_for_ncbi(seq.accession, seq.version)
                    remote = lookup_fasta_residues(mapping, seq.accession, seq.version)
                    stored = stored_map.get(seq.id, "")
                    extra: dict[str, Any] = {}
                    if remote:
                        status = _compare_residues(stored, remote)
                        if status == "VERIFIED_EXACT" and _sha(stored) != _sha(_norm_nt(remote)):
                            extra["note"] = "exact after archival T/U normalisation"
                        elif status == "VERIFIED_EXACT":
                            extra["checksum_match"] = _sha(_norm_nt(remote)) == (seq.checksum or "")
                    elif batch_status:
                        status = batch_status
                    else:
                        status = "TEMPORARILY_UNVERIFIED"
                        extra["detail"] = "accession absent from FASTA batch"
                    _append(
                        out,
                        {
                            "id": str(seq.id),
                            "accession": seq.accession,
                            "version": seq.version,
                            "source": seq.source_key,
                            "type": seq.seq_type.value,
                            "provider": f"ncbi:{db}",
                            "queried": ident,
                            "status": status,
                            "checked_at": _now(),
                            **extra,
                        },
                    )

    if pending_uniprot:
        async with UniProtConnector() as uni:
            for chunk in chunked(pending_uniprot, UNIPROT_CHUNK):
                accs = [s.accession for s in chunk]
                by_acc: dict[str, str] = {}
                batch_err: str | None = None
                try:
                    payload = await uni.get_accessions(accs)
                    for item in payload.get("results") or []:
                        acc = item.get("primaryAccession")
                        seq_val = ((item.get("sequence") or {}).get("value")) or ""
                        if acc and seq_val:
                            by_acc[acc] = seq_val
                except ConnectorNotFound:
                    batch_err = "CONFIRMED_NOT_FOUND"
                except Exception:
                    batch_err = "TEMPORARILY_UNVERIFIED"
                stored_map = await _residues_for([s.id for s in chunk])
                for seq in chunk:
                    remote = by_acc.get(seq.accession)
                    stored = stored_map.get(seq.id, "")
                    if remote:
                        status = _compare_residues(stored, remote)
                    else:
                        status = batch_err or "TEMPORARILY_UNVERIFIED"
                    _append(
                        out,
                        {
                            "id": str(seq.id),
                            "accession": seq.accession,
                            "version": seq.version,
                            "source": seq.source_key,
                            "type": seq.seq_type.value,
                            "provider": "uniprot",
                            "status": status,
                            "checked_at": _now(),
                        },
                    )

    if pending_pdb:
        async with PDBConnector() as pdb:
            stored_map = await _residues_for([s.id for s in pending_pdb])
            for seq in pending_pdb:
                _append(out, await _verify_pdb_polymer(pdb, seq, stored_map.get(seq.id, "")))

    if others:
        async with NCBIConnector() as ncbi:
            for seq in others:
                ident = _ids_for_ncbi(seq.accession, seq.version)
                db = "protein" if seq.seq_type == SequenceType.PROTEIN else "nuccore"
                mapping, batch_status = await _ncbi_fasta(ncbi, db, [ident])
                stored_map = await _residues_for([seq.id])
                remote = lookup_fasta_residues(mapping, seq.accession, seq.version)
                stored = stored_map.get(seq.id, "")
                if remote:
                    status = _compare_residues(stored, remote)
                elif batch_status:
                    status = (
                        "VERIFIED_METADATA_ONLY"
                        if batch_status == "CONFIRMED_NOT_FOUND"
                        else batch_status
                    )
                else:
                    status = "TEMPORARILY_UNVERIFIED"
                _append(
                    out,
                    {
                        "id": str(seq.id),
                        "accession": seq.accession,
                        "version": seq.version,
                        "source": seq.source_key,
                        "type": seq.seq_type.value,
                        "provider": seq.source_key or "unknown",
                        "status": status,
                        "checked_at": _now(),
                    },
                )


def _name_status(stored: str, current: str | None) -> str:
    if not current:
        return "TEMPORARILY_UNVERIFIED"
    a = re.sub(r"\s+", " ", stored.strip().lower())
    b = re.sub(r"\s+", " ", current.strip().lower())
    if a == b:
        return "EXACT"
    return "SYNONYM_ACCEPTABLE"


async def phase_organisms() -> None:
    out = STATE_DIR / "organisms.jsonl"
    done = _load_done(out)
    async with get_sessionmaker()() as session:
        rows = list((await session.execute(select(Organism).order_by(Organism.tax_id))).scalars())
    pending = [o for o in rows if str(o.id) not in done]
    async with NCBIConnector() as ncbi:
        for chunk in chunked(pending, TAX_CHUNK):
            ids = [str(o.tax_id) for o in chunk]
            print(f"taxonomy chunk {ids[0]}… ({len(chunk)})", flush=True)
            try:
                payload = await ncbi.esummary("taxonomy", ids)
                result = payload.get("result") or {}
            except Exception as exc:
                for org in chunk:
                    _append(
                        out,
                        {
                            "id": str(org.id),
                            "tax_id": org.tax_id,
                            "scientific_name": org.scientific_name,
                            "status": "TEMPORARILY_UNVERIFIED",
                            "detail": type(exc).__name__,
                            "checked_at": _now(),
                        },
                    )
                continue
            for org in chunk:
                info = result.get(str(org.tax_id)) or {}
                current = info.get("scientificname") or info.get("scientificName")
                status = _name_status(org.scientific_name, current)
                if info.get("status") == "merged" or info.get("replacedby"):
                    status = "MERGED_TAXID"
                if not info:
                    status = "TEMPORARILY_UNVERIFIED"
                _append(
                    out,
                    {
                        "id": str(org.id),
                        "tax_id": org.tax_id,
                        "scientific_name": org.scientific_name,
                        "remote_name": current,
                        "status": status,
                        "checked_at": _now(),
                    },
                )


def _norm_title(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip().lower().rstrip(".")


async def phase_publications() -> None:
    out = STATE_DIR / "publications.jsonl"
    done = _load_done(out)
    async with get_sessionmaker()() as session:
        rows = list(
            (
                await session.execute(
                    select(Publication).order_by(Publication.pubmed_id.nulls_last())
                )
            ).scalars()
        )
    with_pmid = [p for p in rows if p.pubmed_id and str(p.id) not in done]
    without = [p for p in rows if not p.pubmed_id and str(p.id) not in done]
    for pub in without:
        doi = (pub.doi or "").strip()
        status = "DOI_FORMAT_ONLY" if doi else "NO_PMID"
        _append(
            out,
            {
                "id": str(pub.id),
                "pubmed_id": None,
                "doi": doi or None,
                "status": status,
                "checked_at": _now(),
            },
        )
    async with NCBIConnector() as ncbi:
        for chunk in chunked(with_pmid, PUBMED_CHUNK):
            ids = [str(p.pubmed_id) for p in chunk]
            print(f"pubmed esummary {len(ids)} (first {ids[0]})", flush=True)
            try:
                payload = await ncbi.esummary("pubmed", ids)
                result = payload.get("result") or {}
            except ConnectorNotFound:
                for pub in chunk:
                    _append(
                        out,
                        {
                            "id": str(pub.id),
                            "pubmed_id": pub.pubmed_id,
                            "status": "NOT_FOUND_CONFIRMED",
                            "checked_at": _now(),
                        },
                    )
                continue
            except Exception as exc:
                for pub in chunk:
                    _append(
                        out,
                        {
                            "id": str(pub.id),
                            "pubmed_id": pub.pubmed_id,
                            "status": "TEMPORARILY_UNVERIFIED",
                            "detail": type(exc).__name__,
                            "checked_at": _now(),
                        },
                    )
                continue
            for pub in chunk:
                info = result.get(str(pub.pubmed_id)) or {}
                if not info:
                    status = "TEMPORARILY_UNVERIFIED"
                    detail = "missing esummary row"
                else:
                    remote_title = info.get("title")
                    if _norm_title(pub.title) == _norm_title(remote_title):
                        status = "PMID_VERIFIED"
                        detail = None
                    else:
                        status = "METADATA_MISMATCH"
                        detail = "title differs"
                _append(
                    out,
                    {
                        "id": str(pub.id),
                        "pubmed_id": pub.pubmed_id,
                        "status": status,
                        "detail": detail,
                        "checked_at": _now(),
                    },
                )


def write_summary() -> dict[str, Any]:
    summary = {
        "generated_at": _now(),
        "sequences": _summarize(STATE_DIR / "sequences.jsonl"),
        "organisms": _summarize(STATE_DIR / "organisms.jsonl"),
        "publications": _summarize(STATE_DIR / "publications.jsonl"),
    }
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    (STATE_DIR / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return summary


async def async_main(phase: str) -> int:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    if phase in {"all", "sequences"}:
        await phase_sequences()
        write_summary()
    if phase in {"all", "organisms"}:
        await phase_organisms()
        write_summary()
    if phase in {"all", "publications"}:
        await phase_publications()
        write_summary()
    if phase == "summary":
        write_summary()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--phase",
        choices=("all", "sequences", "organisms", "publications", "summary"),
        default="all",
    )
    args = parser.parse_args()
    return asyncio.run(async_main(args.phase))


if __name__ == "__main__":
    raise SystemExit(main())
