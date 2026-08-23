"""NCBI fetcher (GenBank + RefSeq via E-utilities).

Downloads real GenBank/GenPept flat files and feeds them through the GenBank
parser. RefSeq accessions are attributed to ``ncbi_refseq``, everything else to
``ncbi_genbank`` — provenance follows the actual record, never the request.

Some RefSeq records (notably NG_* antimicrobial-resistance CDS) are stored as
CONTIG assemblies. ``rettype=gb`` then omits ORIGIN. In that case this fetcher
falls back to official FASTA, then ``gbwithparts``, and only persists residues
returned by NCBI after alphabet and length checks. Residues are never invented.
"""

from __future__ import annotations

from app.pipeline.fetchers.base import chunked, import_with_run
from app.pipeline.logging import get_logger
from app.pipeline.models import ImportContext, ImportReport, ParsedSequence
from app.pipeline.parsers.genbank import GenBankParser
from app.pipeline.validation import _NUCLEOTIDE, _PROTEIN
from app.services.connectors.ncbi import NCBIConnector
from app.services.connectors.refseq import is_refseq_accession

logger = get_logger("biowiki.pipeline.fetchers.ncbi")

_EFETCH_CHUNK = 20

_DB_URL_PATH = {"nuccore": "nuccore", "protein": "protein"}
_DB_RETTYPE = {"nuccore": "gb", "protein": "gp"}


def _attribute_source(ps: ParsedSequence, db: str) -> ParsedSequence:
    if is_refseq_accession(ps.accession):
        ps.source_key = "ncbi_refseq"
        ps.source_name = "NCBI RefSeq"
    else:
        ps.source_key = "ncbi_genbank"
        ps.source_name = "NCBI GenBank"
    identifier = f"{ps.accession}.{ps.version}" if ps.version else ps.accession
    ps.source_url = f"https://www.ncbi.nlm.nih.gov/{_DB_URL_PATH[db]}/{identifier}"
    return ps


def _record_id(ps: ParsedSequence) -> str:
    return f"{ps.accession}.{ps.version}" if ps.version else ps.accession


def parse_fasta_residues(text: str) -> dict[str, str]:
    """Map accession and accession.version to uppercase residues from FASTA.

    Keys include both ``NG_047339`` and ``NG_047339.1`` when the header carries
    a version. NCBI headers such as ``>NG_047339.1 …`` and
    ``>ref|NG_047339.1| …`` are accepted. Empty FASTA yields an empty map.
    """
    mapping: dict[str, str] = {}
    header: str | None = None
    chunks: list[str] = []

    def _emit(hdr: str, parts: list[str]) -> None:
        token = hdr.split()[0].strip().rstrip("|")
        if "|" in token:
            token = token.split("|")[-1] or token
        residues = "".join(ch for ch in "".join(parts) if not ch.isspace()).upper()
        if not token or not residues:
            return
        mapping[token] = residues
        if "." in token:
            base, _, ver = token.rpartition(".")
            if ver.isdigit():
                mapping[base] = residues

    for line in text.splitlines():
        if line.startswith(">"):
            if header is not None:
                _emit(header, chunks)
            header = line[1:].strip()
            chunks = []
        elif header is not None:
            chunks.append(line.strip())
    if header is not None:
        _emit(header, chunks)
    return mapping


def lookup_fasta_residues(
    mapping: dict[str, str], accession: str, version: str | None
) -> str | None:
    if version:
        keyed = mapping.get(f"{accession}.{version}")
        if keyed:
            return keyed
    return mapping.get(accession)


def try_attach_official_residues(
    ps: ParsedSequence,
    residues: str,
    *,
    source_label: str,
) -> bool:
    """Attach NCBI residues when they pass alphabet and length checks.

    Returns True only when ``ps.residues`` was set from ``residues``. A stored
    LOCUS length that disagrees with the official sequence is logged and the
    sequence is **not** forced.
    """
    cleaned = "".join(ch for ch in residues if not ch.isspace()).upper()
    if not cleaned:
        logger.warning("Sequence validation failed %s %s: empty residues", source_label, ps.accession)
        return False
    alphabet = _PROTEIN if ps.seq_type in {"protein", "peptide"} else _NUCLEOTIDE
    invalid = set(cleaned) - alphabet
    if invalid:
        logger.warning(
            "Sequence validation failed %s %s: invalid symbols %s",
            source_label,
            ps.accession,
            sorted(invalid),
        )
        return False
    if ps.length is not None and int(ps.length) > 0 and len(cleaned) != int(ps.length):
        logger.warning(
            "Sequence validation failed %s %s: length mismatch stored=%s official=%s; residues not forced",
            source_label,
            ps.accession,
            ps.length,
            len(cleaned),
        )
        return False
    ps.residues = cleaned
    logger.info(
        "Sequence validation successful %s %s (%d residues)",
        source_label,
        ps.accession,
        len(cleaned),
    )
    return True


async def fetch_official_residues(
    ids: list[str],
    *,
    db: str = "nuccore",
    connector: NCBIConnector | None = None,
) -> dict[str, str]:
    """Return accession → residues from NCBI FASTA, then gbwithparts for misses.

    Output keys include bare accessions and versioned ids when present.
    Failed fetches are omitted; callers must not invent replacements.
    """
    owns = connector is None
    conn = connector or NCBIConnector()
    mapping: dict[str, str] = {}
    unique_ids = [i for i in dict.fromkeys(ids) if i]
    try:
        if unique_ids:
            logger.info("FASTA fallback triggered for %d id(s)", len(unique_ids))
        for chunk in chunked(unique_ids, _EFETCH_CHUNK):
            try:
                text = await conn.efetch(db, list(chunk), rettype="fasta", retmode="text")
                mapping.update(parse_fasta_residues(text))
                logger.info("FASTA fetch successful for chunk of %d", len(chunk))
            except Exception:
                logger.exception(
                    "FASTA fallback chunk failed (%d ids); retrying one-by-one",
                    len(chunk),
                )
                for uid in chunk:
                    try:
                        text = await conn.efetch(db, [uid], rettype="fasta", retmode="text")
                        mapping.update(parse_fasta_residues(text))
                        logger.info("FASTA fetch successful %s", uid)
                    except Exception:
                        logger.exception("FASTA fetch skipped uid %s", uid)

        if db != "nuccore":
            return mapping

        still = [uid for uid in unique_ids if uid.split(".")[0] not in mapping and uid not in mapping]
        if not still:
            return mapping

        logger.info("gbwithparts fallback triggered for %d id(s)", len(still))
        parser = GenBankParser()
        context = ImportContext(source_key="ncbi_genbank")
        for uid in still:
            try:
                text = await conn.efetch(db, [uid], rettype="gbwithparts", retmode="text")
            except Exception:
                logger.exception("gbwithparts fetch failed %s", uid)
                continue
            for parsed in parser.parse(text, context):
                if parsed.residues:
                    mapping[parsed.accession] = parsed.residues
                    if parsed.version:
                        mapping[f"{parsed.accession}.{parsed.version}"] = parsed.residues
                    logger.info("gbwithparts fetch successful %s", parsed.accession)
    finally:
        if owns:
            await conn.aclose()
    return mapping


async def _fill_missing_residues(
    conn: NCBIConnector,
    records: list[ParsedSequence],
    db: str,
) -> None:
    missing = [ps for ps in records if not ps.residues]
    if not missing:
        return

    for ps in missing:
        contig = (ps.annotations or {}).get("CONTIG")
        if contig:
            logger.info("CONTIG detected %s; GenBank sequence missing (%s)", ps.accession, contig)
        else:
            logger.info("GenBank sequence missing %s", ps.accession)

    mapping = await fetch_official_residues(
        [_record_id(ps) for ps in missing],
        db=db,
        connector=conn,
    )
    for ps in missing:
        residues = lookup_fasta_residues(mapping, ps.accession, ps.version)
        if residues and try_attach_official_residues(ps, residues, source_label="NCBI"):
            continue
        logger.warning(
            "NCBI provided no recoverable sequence for %s (gb + FASTA/gbwithparts exhausted)",
            ps.accession,
        )


async def fetch_records(
    accessions: list[str] | None = None,
    *,
    term: str | None = None,
    db: str = "nuccore",
    limit: int = 100,
    seq_type: str | None = None,
    connector: NCBIConnector | None = None,
) -> list[ParsedSequence]:
    """Download and parse records by accession list or search term."""
    if db not in _DB_RETTYPE:
        raise ValueError("db must be 'nuccore' or 'protein'")
    if not accessions and not term:
        raise ValueError("Provide accessions or a search term.")

    parser = GenBankParser()
    context = ImportContext(source_key="ncbi_genbank", seq_type=seq_type)

    owns = connector is None
    conn = connector or NCBIConnector()
    parsed: list[ParsedSequence] = []
    try:
        ids = list(accessions or [])
        if term:
            page = await conn.esearch(db, term, retmax=limit)
            ids.extend(hit.identifier for hit in page.hits)
        ids = [i for i in dict.fromkeys(ids) if i]

        for chunk in chunked(ids, _EFETCH_CHUNK):
            try:
                logger.info("NCBI GenBank fetch (%d id(s), rettype=%s)", len(chunk), _DB_RETTYPE[db])
                text = await conn.efetch(
                    db, list(chunk), rettype=_DB_RETTYPE[db], retmode="text"
                )
                for ps in parser.parse(text, context):
                    parsed.append(_attribute_source(ps, db))
            except Exception:
                logger.exception(
                    "ncbi efetch chunk failed (%d ids); retrying one-by-one",
                    len(chunk),
                )
                for uid in chunk:
                    try:
                        logger.info("NCBI GenBank fetch %s", uid)
                        text = await conn.efetch(
                            db, [uid], rettype=_DB_RETTYPE[db], retmode="text"
                        )
                        for ps in parser.parse(text, context):
                            parsed.append(_attribute_source(ps, db))
                    except Exception:
                        logger.exception("ncbi efetch skipped uid %s", uid)

        await _fill_missing_residues(conn, parsed, db)
    finally:
        if owns:
            await conn.aclose()

    logger.info("ncbi fetch: %d record(s) parsed from db=%s", len(parsed), db)
    return parsed


async def ingest(
    accessions: list[str] | None = None,
    *,
    term: str | None = None,
    db: str = "nuccore",
    limit: int = 100,
    seq_type: str | None = None,
    batch_size: int = 200,
) -> ImportReport:
    records = await fetch_records(
        accessions, term=term, db=db, limit=limit, seq_type=seq_type
    )
    return await import_with_run(
        records,
        source_key="ncbi",
        kind="fetch_accessions" if accessions else "fetch_search",
        params={
            "db": db,
            "accessions": accessions,
            "term": term,
            "limit": limit,
            "seq_type": seq_type,
        },
        batch_size=batch_size,
    )
