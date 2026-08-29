"""Canonical Cas9 NGG PAM scan on authentic nucleotide residues.

This is a real, implemented sequence scan: 20 nt spacer + NGG on the same
strand, or the reverse-complement equivalent. It does not estimate on-target
or off-target efficiency. Scores must stay NULL.
"""

from __future__ import annotations

from dataclasses import dataclass

_COMPLEMENT = str.maketrans("ACGT", "TGCA")
_NT = set("ACGT")


@dataclass(frozen=True)
class NggSite:
    start: int  # 0-based spacer start on the plus strand of the source
    end: int  # exclusive
    strand: str
    spacer: str
    pam: str


def _clean_dna(residues: str) -> str:
    seq = "".join(ch for ch in residues.upper() if ch in "ACGTUN")
    return seq.replace("U", "T")


def _revcomp(seq: str) -> str:
    return seq.translate(_COMPLEMENT)[::-1]


def find_cas9_ngg_sites(
    residues: str,
    *,
    spacer_len: int = 20,
    max_sites: int = 5,
) -> list[NggSite]:
    """Return up to ``max_sites`` NGG spacers copied from ``residues``.

    Sites with non-ACGT spacers are skipped. Nothing is invented.
    """
    seq = _clean_dna(residues)
    if spacer_len < 15 or len(seq) < spacer_len + 3:
        return []
    found: list[NggSite] = []
    seen: set[tuple[int, str]] = set()

    for i in range(0, len(seq) - spacer_len - 2):
        pam = seq[i + spacer_len : i + spacer_len + 3]
        if len(pam) != 3 or pam[1:] != "GG" or pam[0] not in _NT:
            continue
        spacer = seq[i : i + spacer_len]
        if set(spacer) - _NT:
            continue
        key = (i, "+")
        if key in seen:
            continue
        seen.add(key)
        found.append(NggSite(start=i, end=i + spacer_len, strand="+", spacer=spacer, pam=pam))
        if len(found) >= max_sites:
            return found

    # Minus strand: CCN on plus is NGG on minus; spacer is reverse complement
    # of the 20 nt immediately 3' of that CCN on plus.
    for i in range(0, len(seq) - spacer_len - 2):
        plus_pam = seq[i : i + 3]
        if len(plus_pam) != 3 or plus_pam[:2] != "CC" or plus_pam[2] not in _NT:
            continue
        plus_spacer = seq[i + 3 : i + 3 + spacer_len]
        if len(plus_spacer) != spacer_len or set(plus_spacer) - _NT:
            continue
        spacer = _revcomp(plus_spacer)
        pam = _revcomp(plus_pam)
        key = (i + 3, "-")
        if key in seen:
            continue
        seen.add(key)
        found.append(
            NggSite(
                start=i + 3,
                end=i + 3 + spacer_len,
                strand="-",
                spacer=spacer,
                pam=pam,
            )
        )
        if len(found) >= max_sites:
            return found
    return found
