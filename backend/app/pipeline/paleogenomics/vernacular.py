"""Verified vernacular names. Never invents a common name.

English catalogue names are the curated BioWiki vernacular.
Other locales are accepted only from Wikidata taxon common names or labels
that are not scientific names and do not contradict the stored species.
"""

from __future__ import annotations

import re

LOCALES: tuple[str, ...] = (
    "pt-BR",
    "en-GB",
    "es-ES",
    "de-DE",
    "it-IT",
    "zh-CN",
    "ja-JP",
    "ar-SA",
    "fr-FR",
    "ru-RU",
    "hi-IN",
)

_LANG_TO_LOCALE: dict[str, str] = {
    "pt": "pt-BR",
    "pt-br": "pt-BR",
    "en": "en-GB",
    "es": "es-ES",
    "de": "de-DE",
    "it": "it-IT",
    "zh": "zh-CN",
    "zh-hans": "zh-CN",
    "zh-cn": "zh-CN",
    "ja": "ja-JP",
    "ar": "ar-SA",
    "fr": "fr-FR",
    "ru": "ru-RU",
    "hi": "hi-IN",
}

# Wikidata P225 values that correspond to a BioWiki paleogenomics slug.
# Homo sapiens neanderthalensis is intentionally absent: a Wikidata label on
# that string has been the unrelated Dingcun hominin name.
WIKIDATA_SCIENTIFIC_TO_SLUG: dict[str, str] = {
    "Homo neanderthalensis": "homo-neanderthalensis",
    "Thylacinus cynocephalus": "thylacinus-cynocephalus",
    "Coelodonta antiquitatis": "coelodonta-antiquitatis",
    "Raphus cucullatus": "raphus-cucullatus",
    "Mammuthus primigenius": "mammuthus-primigenius",
    "Mammut americanum": "mammut-americanum",
    "Smilodon populator": "smilodon-populator",
    "Bos primigenius": "bos-primigenius",
    "Equus quagga quagga": "equus-quagga-quagga",
    "Ectopistes migratorius": "ectopistes-migratorius",
    "Hydrodamalis gigas": "hydrodamalis-gigas",
    "Pinguinus impennis": "pinguinus-impennis",
    "Dinornis robustus": "dinornis-robustus",
    "Megaloceros giganteus": "megaloceros-giganteus",
    "Ursus spelaeus": "ursus-spelaeus",
}

# Labels that name a different population or island than the stored taxon.
_REJECT_SUBSTRINGS: dict[str, tuple[str, ...]] = {
    "dinornis-robustus": (
        "isla norte",
        "isola del nord",
        "north island",
        "île du nord",
        "ile du nord",
    ),
    "homo-neanderthalensis": ("丁村",),
}

_PROPERTY_RANK = {"P1843": 2, "rdfs:label": 1}
_LANG_RANK = {"pt-br": 2, "pt": 1, "zh-hans": 2, "zh-cn": 2, "zh": 1}


def locale_or_none(value: str | None) -> str | None:
    if value in LOCALES:
        return value
    return None


def looks_like_scientific_name(name: str, scientific_name: str) -> bool:
    """True when the string is the binomial/trinomial, not a vernacular."""
    cleaned = re.sub(r"\s+", " ", name).strip()
    scientific = re.sub(r"\s+", " ", scientific_name).strip()
    if not cleaned or cleaned.casefold() == scientific.casefold():
        return True
    parts = cleaned.split(" ")
    genus = scientific.split(" ")[0]
    if len(parts) >= 2 and parts[0].casefold() == genus.casefold():
        rest_latin = all(re.fullmatch(r"[A-Za-z][a-z.'’-]*", part) for part in parts[1:])
        if rest_latin and parts[0][:1].isupper():
            return True
    return False


def accept_wikidata_name(
    *,
    slug: str,
    scientific_name: str,
    name: str,
    lang: str,
) -> str | None:
    locale = _LANG_TO_LOCALE.get(lang.strip().lower())
    if locale is None:
        return None
    if looks_like_scientific_name(name, scientific_name):
        return None
    folded = name.casefold()
    for banned in _REJECT_SUBSTRINGS.get(slug, ()):
        if banned.casefold() in folded or banned in name:
            return None
    return locale


def prefer_candidate(current: dict[str, str] | None, candidate: dict[str, str]) -> dict[str, str]:
    if current is None:
        return candidate
    current_rank = (
        _PROPERTY_RANK.get(current.get("source_property", ""), 0),
        _LANG_RANK.get(current.get("lang", ""), 0),
    )
    next_rank = (
        _PROPERTY_RANK.get(candidate.get("source_property", ""), 0),
        _LANG_RANK.get(candidate.get("lang", ""), 0),
    )
    return candidate if next_rank > current_rank else current


def resolve_display(
    locale: str | None,
    by_locale: dict[str, dict[str, str]],
    *,
    english_name: str | None,
    scientific_name: str,
) -> dict[str, str | bool] | None:
    """Pick a verified vernacular. Never returns the scientific name as a translation."""
    chosen = locale_or_none(locale) or "en-GB"
    row = by_locale.get(chosen)
    if row and row.get("name") and not looks_like_scientific_name(row["name"], scientific_name):
        return {**row, "fallback": False}
    english = (by_locale.get("en-GB") or {}).get("name") or english_name
    if english and not looks_like_scientific_name(english, scientific_name):
        source = by_locale.get("en-GB") or {}
        return {
            "name": english,
            "locale": "en-GB",
            "source": source.get("source") or "organism.common_name",
            "source_url": source.get("source_url") or "",
            "fallback": chosen != "en-GB",
        }
    return None
