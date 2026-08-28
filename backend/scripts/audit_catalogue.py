"""Read-only scientific catalogue audit against the public API (or a local API).

Never INSERT/UPDATE/DELETE. Network failures are TEMPORARILY_UNVERIFIED.
Run: python -m scripts.audit_catalogue
"""

from __future__ import annotations

import json
import os
import re
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from typing import Any

API = os.environ.get("BIOWIKI_API_URL", "https://biowiki-api.vercel.app/api/v1").rstrip("/")
UA = "BioWikiCatalogueAudit/1.0 (read-only; https://github.com/gabrielusp3-rgb/BioWiki)"
CTX = ssl.create_default_context()

# RefSeq / GenBank prefix families used only as heuristic flags, never as
# sole proof of misclassification.
_TRANSCRIPT = re.compile(r"^(N[MR]|X[MR])_")
_PROTEIN_REFSEQ = re.compile(r"^(NP|XP|YP|WP)_")
_GENOMIC_REFSEQ = re.compile(r"^(N[CGZ]|NW|NT)_")
_UNIPROT = re.compile(r"^[OPQ][0-9][A-Z0-9]{3}[0-9]$|^[A-NR-Z][0-9](?:[A-Z][A-Z0-9]{2}[0-9]){1,2}$")

_NUCLEOTIDE = set("ACGTUNRYSWKMBDHV-")
_PROTEIN_ALPH = set("ACDEFGHIKLMNPQRSTVWYBXZJUO*-")
_STRICT_NUC = set("ACGTUN")

_RETRYABLE = (429, 500, 502, 503, 504)


class TempUnverified(Exception):
    pass


def _get(url: str, retries: int = 3) -> Any:
    delay = 1.0
    last: Exception | None = None
    for _ in range(retries):
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, context=CTX, timeout=25) as resp:
                raw = resp.read()
                ctype = resp.headers.get("Content-Type", "")
                if "json" in ctype or raw[:1] in (b"{", b"["):
                    return json.loads(raw.decode("utf-8"))
                return raw.decode("utf-8")
        except urllib.error.HTTPError as exc:
            last = exc
            if exc.code in _RETRYABLE:
                retry_after = exc.headers.get("Retry-After") if exc.headers else None
                wait = float(retry_after) if retry_after and str(retry_after).isdigit() else delay
                time.sleep(wait)
                delay = min(delay * 2, 30)
                continue
            raise
        except (urllib.error.URLError, TimeoutError, TimeoutError) as exc:
            last = exc
            time.sleep(delay)
            delay = min(delay * 2, 30)
    raise TempUnverified(str(last))


def paginate(path: str, key: str = "results") -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    cursor: str | None = None
    while True:
        params: dict[str, str] = {"limit": "100"}
        if cursor:
            params["cursor"] = cursor
        qs = urllib.parse.urlencode(params)
        url = f"{API}{path}{'&' if '?' in path else '?'}{qs}"
        body = _get(url)
        chunk = body.get(key) or body.get("results") or body.get("organisms") or []
        items.extend(chunk)
        cursor = body.get("nextCursor") or body.get("next_cursor")
        if not cursor or not chunk:
            break
    return items


def prefix_family(accession: str) -> str:
    acc = accession.split(".")[0]
    if _TRANSCRIPT.match(acc):
        return "refseq_transcript"
    if _PROTEIN_REFSEQ.match(acc):
        return "refseq_protein"
    if _GENOMIC_REFSEQ.match(acc):
        return "refseq_genomic"
    if acc.startswith("GCF_") or acc.startswith("GCA_"):
        return "assembly"
    if _UNIPROT.match(acc):
        return "uniprot"
    if re.match(r"^[0-9A-Z]{4}_", acc):
        return "pdb_entity"
    if acc.startswith("RF"):
        return "rfam"
    return "other"


def alphabet_kind(residues: str | None) -> str:
    if not residues:
        return "empty"
    seq = residues.upper()
    symbols = set(seq)
    if not symbols:
        return "empty"
    if symbols <= _PROTEIN_ALPH and not symbols <= _NUCLEOTIDE:
        return "protein"
    if symbols <= _STRICT_NUC:
        has_t = "T" in symbols
        has_u = "U" in symbols
        if has_t and has_u:
            return "nucleotide_tu"
        if has_u and not has_t:
            return "nucleotide_u"
        return "nucleotide_t_or_acg"
    if symbols <= _NUCLEOTIDE:
        return "nucleotide_iupac"
    extra = symbols - _NUCLEOTIDE - _PROTEIN_ALPH
    if extra:
        return "invalid"
    return "mixed"


def infer_group(lineage: list[str] | None) -> str | None:
    joined = " ".join(lineage or []).lower()
    if not joined:
        return None
    if "virus" in joined or "viruses" in joined:
        return "virus"
    if "archaea" in joined:
        return "archaea"
    if "bacteria" in joined:
        return "bacteria"
    if "fungi" in joined:
        return "fungus"
    if "viridiplantae" in joined or "plantae" in joined:
        return "plant"
    if "metazoa" in joined:
        return "animal"
    if "eukaryota" in joined and (
        "alveolata" in joined or "euglenozoa" in joined or "apicomplexa" in joined
    ):
        return "protozoan"
    return None


def ncbi_esummary(ids: list[str], db: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for i in range(0, len(ids), 100):
        chunk = ids[i : i + 100]
        print(f"  ncbi {db} batch {i // 100 + 1} ({len(chunk)})", flush=True)
        qs = urllib.parse.urlencode(
            {
                "db": db,
                "id": ",".join(chunk),
                "retmode": "json",
            }
        )
        url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?{qs}"
        try:
            body = _get(url)
        except TempUnverified:
            for acc in chunk:
                out[acc] = {"status": "TEMPORARILY_UNVERIFIED"}
            time.sleep(1)
            continue
        result = body.get("result") or {}
        uids = result.get("uids") or []
        found: set[str] = set()
        for uid in uids:
            rec = result.get(uid) or {}
            acc = rec.get("accessionversion") or rec.get("caption") or ""
            bare = str(acc).split(".")[0]
            payload = {
                "status": "VERIFIED",
                "caption": rec.get("caption"),
                "accessionversion": rec.get("accessionversion"),
                "taxid": rec.get("taxid"),
                "organism": rec.get("organism"),
                "slen": rec.get("slen"),
                "moltype": rec.get("moltype") or rec.get("mol"),
                "title": rec.get("title"),
                "sourcedb": rec.get("sourcedb"),
            }
            out[bare] = payload
            found.add(bare)
            if acc:
                out[str(acc)] = payload
        for acc in chunk:
            bare = acc.split(".")[0]
            if bare not in found and acc not in out:
                # esummary returns empty uids for unknown ids without error
                out[bare] = {"status": "NOT_FOUND"}
        time.sleep(0.4)
    return out


def uniprot_verify(accessions: list[str]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for i in range(0, len(accessions), 40):
        chunk = accessions[i : i + 40]
        query = " OR ".join(f"accession:{acc}" for acc in chunk)
        qs = urllib.parse.urlencode({"query": query, "format": "json", "size": str(len(chunk))})
        url = f"https://rest.uniprot.org/uniprotkb/search?{qs}"
        print(f"  uniprot batch {i // 40 + 1} ({len(chunk)})", flush=True)
        try:
            body = _get(url)
        except (TempUnverified, urllib.error.HTTPError):
            for acc in chunk:
                out[acc] = {"status": "TEMPORARILY_UNVERIFIED"}
            continue
        results = body.get("results") or [] if isinstance(body, dict) else []
        found: set[str] = set()
        for rec in results:
            acc = rec.get("primaryAccession") or ""
            out[acc] = {
                "status": "VERIFIED",
                "organism": (rec.get("organism") or {}).get("scientificName"),
                "taxid": (rec.get("organism") or {}).get("taxonId"),
                "reviewed": rec.get("entryType"),
                "length": (rec.get("sequence") or {}).get("length"),
            }
            found.add(acc)
        for acc in chunk:
            if acc not in found:
                out[acc] = {"status": "NOT_FOUND"}
        time.sleep(0.3)
    return out


def main() -> None:
    skip_external = "--skip-external" in sys.argv
    report: dict[str, Any] = {"api": API, "suspicious": [], "verification": {}}

    stats = _get(f"{API}/statistics")
    integrity = _get(f"{API}/statistics/integrity")
    report["statistics"] = stats
    report["integrity"] = integrity

    dna = paginate("/sequences?type=dna")
    rna = paginate("/sequences?type=rna")
    crispr = paginate("/crispr")
    proteins = paginate("/proteins")
    virus = paginate("/viruses")
    genomes = paginate("/genomes")
    organisms = paginate("/organisms", key="organisms")

    typed = {
        "dna": dna,
        "rna": rna,
        "crispr": crispr,
        "protein": proteins,
        "virus": virus,
    }
    report["counts"] = {k: len(v) for k, v in typed.items()}
    report["counts"]["genome_records"] = len(genomes)
    report["counts"]["organisms"] = len(organisms)
    report["counts"]["publications_stat"] = stats.get("publications")

    # seq_type × source, organism, feature
    matrices: dict[str, Any] = {}
    for kind, rows in typed.items():
        by_source = Counter(r.get("source") or "?" for r in rows)
        by_org = Counter(r.get("organism") or "?" for r in rows)
        by_prefix = Counter(prefix_family(r.get("accession") or "") for r in rows)
        extra = {}
        if kind == "dna":
            extra["molecule_type"] = Counter(str(r.get("moleculeType") or r.get("molecule_type") or "?") for r in rows)
        if kind == "rna":
            extra["rna_class"] = Counter(str(r.get("rnaClass") or r.get("rna_class") or "?") for r in rows)
        if kind == "virus":
            extra["molecule"] = Counter(str(r.get("molecule") or "?") for r in rows)
            extra["genome_type"] = Counter(str(r.get("genomeType") or r.get("genome_type") or "?") for r in rows)
            extra["family"] = Counter(str(r.get("family") or "?") for r in rows)
        if kind == "crispr":
            extra["system"] = Counter(str(r.get("system") or "?") for r in rows)
            extra["missing_pam"] = sum(1 for r in rows if not r.get("pam"))
        if kind == "protein":
            extra["reviewed"] = Counter(str(r.get("reviewed")) for r in rows)
        matrices[kind] = {
            "source": dict(by_source),
            "prefix": dict(by_prefix),
            "top_organisms": by_org.most_common(15),
            **{k: (dict(v) if isinstance(v, Counter) else v) for k, v in extra.items()},
        }
    report["matrices"] = matrices

    suspicious: list[dict[str, Any]] = []

    def flag(kind: str, row: dict[str, Any], reason: str, expected: str | None = None) -> None:
        suspicious.append(
            {
                "seq_type": kind,
                "accession": row.get("accession"),
                "source": row.get("source"),
                "organism": row.get("organism"),
                "length": row.get("length") or row.get("guideLength") or row.get("guide_length"),
                "reason": reason,
                "expected": expected,
            }
        )

    # Accession-family vs category (heuristic → investigate, not auto-delete)
    for row in dna:
        fam = prefix_family(row.get("accession") or "")
        if fam == "refseq_transcript":
            flag("dna", row, "RefSeq transcript prefix in DNA category", "rna")
        if fam == "refseq_protein" or fam == "uniprot":
            flag("dna", row, "protein accession in DNA category", "protein")
        if fam == "assembly":
            flag("dna", row, "assembly accession stored as sequence DNA", "genome")
    for row in rna:
        fam = prefix_family(row.get("accession") or "")
        if fam == "refseq_genomic":
            flag("rna", row, "genomic RefSeq prefix in RNA category", "dna")
        if fam == "refseq_protein" or fam == "uniprot":
            flag("rna", row, "protein accession in RNA category", "protein")
        if fam == "refseq_transcript":
            pass  # expected
    for row in proteins:
        fam = prefix_family(row.get("accession") or "")
        if fam == "refseq_transcript" or fam == "refseq_genomic":
            flag("protein", row, "nucleotide accession in protein category", "dna/rna")
    for row in virus:
        if not row.get("family"):
            flag("virus", row, "virus without family")
        mol = (row.get("molecule") or "").lower()
        if mol not in {"dna", "rna"}:
            flag("virus", row, f"virus molecule not dna/rna: {mol!r}")
    for row in crispr:
        if not row.get("system"):
            flag("crispr", row, "crispr without cas system")

    # Duplicate accessions within and across categories
    seen: dict[str, list[str]] = defaultdict(list)
    for kind, rows in typed.items():
        for row in rows:
            acc = row.get("accession")
            if acc:
                seen[acc].append(kind)
    cross = {acc: kinds for acc, kinds in seen.items() if len(kinds) > 1}
    report["duplicate_accessions_across_types"] = cross
    for acc, kinds in cross.items():
        suspicious.append(
            {
                "seq_type": "+".join(kinds),
                "accession": acc,
                "reason": "same accession in multiple categories",
                "expected": "single semantic category or distinct provenance keys",
            }
        )

    genome_acc = [g.get("accession") for g in genomes]
    report["genome_accessions"] = genome_acc
    report["duplicate_genome_accessions"] = [
        acc for acc, n in Counter(genome_acc).items() if n > 1
    ]
    overlap_seq_genome = sorted(set(seen) & set(genome_acc))
    report["sequence_accessions_also_assemblies"] = overlap_seq_genome

    # Organism group vs lineage
    org_issues = []
    by_tax: dict[int, list[str]] = defaultdict(list)
    by_group = Counter()
    for org in organisms:
        tax = org.get("taxId") or org.get("tax_id")
        if tax:
            by_tax[int(tax)].append(org.get("scientificName") or org.get("scientific_name") or "")
        group = org.get("group")
        by_group[str(group)] += 1
        inferred = infer_group(org.get("lineage") or [])
        if inferred and group and inferred != group:
            org_issues.append(
                {
                    "tax_id": tax,
                    "scientific_name": org.get("scientificName"),
                    "stored_group": group,
                    "inferred_group": inferred,
                    "lineage": org.get("lineage"),
                }
            )
        if group == "bacteria" and inferred is None:
            org_issues.append(
                {
                    "tax_id": tax,
                    "scientific_name": org.get("scientificName"),
                    "stored_group": group,
                    "inferred_group": None,
                    "lineage": org.get("lineage"),
                    "reason": "bacteria stored without lineage support — possible fallback",
                }
            )
    report["organism_groups"] = dict(by_group)
    report["duplicate_tax_ids"] = {str(k): v for k, v in by_tax.items() if len(v) > 1}
    report["organism_group_mismatches"] = org_issues

    # Residue alphabet from bulk JSON (no mutations)
    dumps: dict[str, list] = {}
    for kind in ("dna", "rna", "protein", "crispr", "virus"):
        url = f"{API}/download/sequences?format=json&type={kind}&limit=10000"
        try:
            body = _get(url)
            dumps[kind] = body if isinstance(body, list) else []
        except TempUnverified as exc:
            dumps[kind] = []
            report.setdefault("download_errors", {})[kind] = str(exc)
        time.sleep(0.2)

    alph: dict[str, Counter] = {}
    checksum_clusters: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for kind, rows in dumps.items():
        c = Counter()
        for row in rows:
            seq = row.get("sequence") or ""
            kind_a = alphabet_kind(seq)
            c[kind_a] += 1
            if kind in {"protein"} and kind_a.startswith("nucleotide"):
                flag("protein", row, f"protein residues look nucleotide ({kind_a})", "protein alphabet")
            if kind in {"dna", "rna", "crispr", "virus"} and kind_a == "protein":
                flag(kind, row, "nucleotide category with protein-like alphabet")
            if kind in {"dna", "rna", "crispr", "virus"} and kind_a == "invalid":
                flag(kind, row, "residues contain symbols outside IUPAC nucleotide+protein")
            length = row.get("length")
            if seq and length is not None and len(seq) != int(length):
                flag(kind, row, f"length {length} != residue count {len(seq)}")
            if seq:
                import hashlib

                digest = hashlib.sha256(seq.encode("ascii", "ignore")).hexdigest()
                checksum_clusters[digest].append((kind, row.get("accession") or ""))
        alph[kind] = c
    report["residue_alphabets"] = {k: dict(v) for k, v in alph.items()}
    same_checksum = {
        digest[:12]: pairs
        for digest, pairs in checksum_clusters.items()
        if len(pairs) > 1
    }
    report["checksum_cluster_count"] = len(same_checksum)
    report["checksum_clusters_sample"] = dict(list(same_checksum.items())[:30])

    report["suspicious"] = suspicious
    report["suspicious_count"] = len(suspicious)
    report.setdefault("verification", {
        "summary": {},
        "not_found": {},
        "temporarily_unverified_counts": {},
    })
    report.setdefault("ncbi_moltype_flags", [])
    report.setdefault("ncbi_moltype_flag_count", 0)

    def _print_local() -> None:
        print(json.dumps({k: report[k] for k in (
            "counts", "matrices", "suspicious_count", "duplicate_accessions_across_types",
            "duplicate_genome_accessions", "sequence_accessions_also_assemblies",
            "organism_groups", "duplicate_tax_ids", "residue_alphabets",
            "checksum_cluster_count", "integrity",
        ) if k in report}, indent=2, default=str), flush=True)
        print("\n--- organism_group_mismatches ---", flush=True)
        print(json.dumps(report["organism_group_mismatches"], indent=2, default=str)[:8000], flush=True)
        print("\n--- suspicious (first 80) ---", flush=True)
        print(json.dumps(report["suspicious"][:80], indent=2, default=str), flush=True)

    _print_local()
    if skip_external:
        print("\nEXTERNAL: skipped (--skip-external)", flush=True)
        return

    # External verification — NCBI for nucleotide-like, UniProt for protein-like
    nuc_acc: list[str] = []
    prot_acc: list[str] = []
    for kind, rows in typed.items():
        for row in rows:
            acc = row.get("accession") or ""
            fam = prefix_family(acc)
            if kind == "protein" or fam in {"uniprot", "refseq_protein"}:
                if fam == "uniprot":
                    prot_acc.append(acc)
                elif fam == "refseq_protein":
                    nuc_acc.append(acc)  # protein db
            elif fam != "pdb_entity" and fam != "rfam" and fam != "other":
                nuc_acc.append(acc)
            elif kind in {"dna", "rna", "virus", "crispr"} and fam in {"other", "rfam"}:
                nuc_acc.append(acc)

    verification = {
        "ncbi_nuccore": {},
        "ncbi_protein": {},
        "uniprot": {},
        "summary": Counter(),
    }

    # Limit NCBI to unique accessions; verify all — 1542 is batchable
    unique_nuc = sorted(set(nuc_acc))
    unique_prot_refseq = sorted({a for a in unique_nuc if _PROTEIN_REFSEQ.match(a.split(".")[0])})
    unique_nuccore = sorted(set(unique_nuc) - set(unique_prot_refseq))
    unique_uniprot = sorted(set(prot_acc))

    print(f"Verifying NCBI nuccore n={len(unique_nuccore)}", flush=True)
    try:
        verification["ncbi_nuccore"] = ncbi_esummary(unique_nuccore, "nuccore")
    except TempUnverified as exc:
        verification["ncbi_nuccore_error"] = str(exc)
    print(f"Verifying NCBI protein n={len(unique_prot_refseq)}", flush=True)
    try:
        verification["ncbi_protein"] = ncbi_esummary(unique_prot_refseq, "protein")
    except TempUnverified as exc:
        verification["ncbi_protein_error"] = str(exc)
    print(f"Verifying UniProt n={len(unique_uniprot)}", flush=True)
    try:
        verification["uniprot"] = uniprot_verify(unique_uniprot)
    except TempUnverified as exc:
        verification["uniprot_error"] = str(exc)

    for bucket in ("ncbi_nuccore", "ncbi_protein", "uniprot"):
        for rec in (verification.get(bucket) or {}).values():
            if isinstance(rec, dict) and "status" in rec:
                verification["summary"][rec["status"]] += 1
    verification["summary"] = dict(verification["summary"])
    report["verification"] = {
        "summary": verification["summary"],
        "not_found": {
            bucket: [
                acc
                for acc, rec in (verification.get(bucket) or {}).items()
                if isinstance(rec, dict) and rec.get("status") == "NOT_FOUND"
            ]
            for bucket in ("ncbi_nuccore", "ncbi_protein", "uniprot")
        },
        "temporarily_unverified_counts": {
            bucket: sum(
                1
                for rec in (verification.get(bucket) or {}).values()
                if isinstance(rec, dict) and rec.get("status") == "TEMPORARILY_UNVERIFIED"
            )
            for bucket in ("ncbi_nuccore", "ncbi_protein", "uniprot")
        },
    }

    # Molecule-type mismatches vs NCBI moltype (advisory)
    mol_mismatches = []
    by_acc_type = {row["accession"]: "dna" for row in dna if row.get("accession")}
    by_acc_type.update({row["accession"]: "rna" for row in rna if row.get("accession")})
    by_acc_type.update({row["accession"]: "virus" for row in virus if row.get("accession")})
    for acc, rec in (verification.get("ncbi_nuccore") or {}).items():
        if not isinstance(rec, dict) or rec.get("status") != "VERIFIED":
            continue
        kind = by_acc_type.get(acc)
        mol = str(rec.get("moltype") or "").lower()
        if not kind or not mol:
            continue
        if kind == "dna" and "rna" in mol and _TRANSCRIPT.match(acc.split(".")[0]):
            mol_mismatches.append(
                {"accession": acc, "stored": kind, "ncbi_moltype": rec.get("moltype"), "note": "transcript moltype vs DNA"}
            )
        if kind == "rna" and mol in {"dna", "genomic"} and "rna" not in mol:
            mol_mismatches.append(
                {"accession": acc, "stored": kind, "ncbi_moltype": rec.get("moltype"), "note": "genomic moltype vs RNA"}
            )
        stored_len = None
        for collection in (dna, rna, virus, crispr):
            hit = next((r for r in collection if r.get("accession") == acc), None)
            if hit:
                stored_len = hit.get("length") or hit.get("guideLength")
                break
        slen = rec.get("slen")
        if stored_len is not None and slen is not None and int(stored_len) != int(slen):
            mol_mismatches.append(
                {
                    "accession": acc,
                    "stored": kind,
                    "stored_length": stored_len,
                    "ncbi_slen": slen,
                    "note": "length mismatch vs NCBI",
                }
            )
    report["ncbi_moltype_flags"] = mol_mismatches[:80]
    report["ncbi_moltype_flag_count"] = len(mol_mismatches)

    print(json.dumps({k: report[k] for k in (
        "counts", "matrices", "suspicious_count", "duplicate_accessions_across_types",
        "duplicate_genome_accessions", "sequence_accessions_also_assemblies",
        "organism_groups", "duplicate_tax_ids", "residue_alphabets",
        "checksum_cluster_count", "verification", "ncbi_moltype_flag_count",
        "integrity",
    ) if k in report}, indent=2, default=str))
    print("\n--- organism_group_mismatches ---")
    print(json.dumps(report["organism_group_mismatches"], indent=2, default=str)[:8000])
    print("\n--- suspicious (first 80) ---")
    print(json.dumps(report["suspicious"][:80], indent=2, default=str))
    print("\n--- not_found ---")
    print(json.dumps(report["verification"].get("not_found"), indent=2))
    print("\n--- ncbi_moltype_flags sample ---")
    print(json.dumps(report["ncbi_moltype_flags"][:40], indent=2, default=str))


if __name__ == "__main__":
    main()
