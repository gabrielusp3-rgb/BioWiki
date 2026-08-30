"""Paleogenomic scientific semantics. No invented accessions or molecule types."""

from __future__ import annotations

import re

_COMPLETE_MT_RE = re.compile(
    r"(complete\s+(mitochondrial|mitogenome|mtDNA)\s+genome)"
    r"|((mitochondrion|mitochondrial|mitogenome|mtdna).{0,48}complete\s+genome)"
    r"|(complete\s+genome.{0,48}(mitochondrion|mitochondrial|mitogenome))",
    re.I,
)
_PARTIAL_RE = re.compile(r"\b(partial|fragment|cds|gene)\b", re.I)


def normalize_doi(value: str | None) -> str | None:
    if not value:
        return None
    text = value.strip().lower()
    text = text.removeprefix("https://doi.org/").removeprefix("http://doi.org/")
    text = text.removeprefix("doi:")
    return text or None


def is_complete_mitogenome(*, definition: str | None, length: int | None) -> bool:
    """A complete mt genome is both named complete and size-appropriate.

    Partial fragments must not be promoted automatically.
    """
    if length is None or length < 14000 or length > 20000:
        return False
    text = definition or ""
    if _PARTIAL_RE.search(text) and not _COMPLETE_MT_RE.search(text):
        return False
    return bool(_COMPLETE_MT_RE.search(text))


def sequence_length_allowed_for_catalogue(length: int | None, *, molecule: str = "dna") -> bool:
    """Reject chromosome-scale residues. Assemblies belong in genome_records."""
    if length is None or length <= 0:
        return False
    if molecule == "protein":
        return length <= 8000
    return length <= 100_000


def introgression_is_not_ancient_specimen(*, modern_tax_id: int, archaic_source: str) -> bool:
    """Introgression rows describe Homo sapiens ancestry segments."""
    del archaic_source
    return modern_tax_id == 9606


def living_relative_is_not_extinct(scientific_name: str, extinct_name: str) -> bool:
    return scientific_name.strip().lower() != extinct_name.strip().lower()


def sra_run_is_not_a_sequence_accession(accession: str) -> bool:
    token = accession.strip().upper()
    return token.startswith(("SRR", "ERR", "DRR"))


_BIOPROJECT_RE = re.compile(r"\b(PRJ[A-Z]{2}\d+)\b", re.I)
_BIOSAMPLE_RE = re.compile(r"\b((?:SAMN|SAMD|SAMEA|SAME)\d+)\b", re.I)
_VOUCHER_RE = re.compile(
    r"\b(?:voucher|isolate)\s+([A-Za-z0-9][A-Za-z0-9._/-]{1,48})",
    re.I,
)


def specimen_label_from_definition(*texts: str | None) -> str | None:
    """Copy an explicit voucher/isolate token from source text. Never infers one."""
    blob = " ".join(part for part in texts if part)
    match = _VOUCHER_RE.search(blob)
    if not match:
        return None
    return match.group(1)[:160]


def extract_project_accessions(*texts: str | None) -> tuple[list[str], list[str]]:
    """Pull BioProject/BioSample accessions from source text. Never invents them."""
    blob = " ".join(part for part in texts if part)
    projects = list(dict.fromkeys(m.group(1).upper() for m in _BIOPROJECT_RE.finditer(blob)))
    samples = list(dict.fromkeys(m.group(1).upper() for m in _BIOSAMPLE_RE.finditer(blob)))
    return projects, samples


def species_search_names(
    scientific_name: str,
    common_name: str,
    synonyms: tuple[str, ...] = (),
) -> tuple[str, ...]:
    """Distinct names long enough to match literature without trivial tokens."""
    seen: set[str] = set()
    names: list[str] = []
    for raw in (scientific_name, common_name, *synonyms):
        text = " ".join(str(raw).split())
        key = text.casefold()
        if len(text) < 3 or key in seen:
            continue
        seen.add(key)
        names.append(text)
    return tuple(names)
