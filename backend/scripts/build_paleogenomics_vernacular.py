"""Download Wikidata vernacular names for Paleogenomics taxa and write a reviewed JSON file.

Does not write the database. Rejects scientific names and known mis-associations.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.pipeline.paleogenomics.catalogue import SPECIES
from app.pipeline.paleogenomics.vernacular import (
    WIKIDATA_SCIENTIFIC_TO_SLUG,
    accept_wikidata_name,
    prefer_candidate,
)

OUT = Path(__file__).resolve().parents[1] / "app" / "data" / "paleogenomics_vernacular.json"
LANGS = ("pt", "pt-br", "en", "es", "de", "it", "zh", "zh-hans", "zh-cn", "ja", "ar", "fr", "ru", "hi")


def _query() -> list[dict[str, str]]:
    names = " ".join(f'"{name}"' for name in WIKIDATA_SCIENTIFIC_TO_SLUG)
    lang_filter = ", ".join(f'"{lang}"' for lang in LANGS)
    sparql = f"""
SELECT ?item ?sci ?name ?lang ?prop WHERE {{
  VALUES ?sci {{ {names} }}
  ?item wdt:P225 ?sci .
  {{
    ?item wdt:P1843 ?name .
    BIND("P1843" AS ?prop)
  }} UNION {{
    ?item rdfs:label ?name .
    BIND("rdfs:label" AS ?prop)
  }}
  BIND(LANG(?name) AS ?lang)
  FILTER(?lang IN ({lang_filter}))
}}
"""
    url = "https://query.wikidata.org/sparql?" + urlencode({"query": sparql})
    request = Request(
        url,
        headers={
            "Accept": "application/sparql-results+json",
            "User-Agent": "BioWiki/1.0 (https://github.com/gabrielusp3-rgb/BioWiki)",
        },
    )
    with urlopen(request, timeout=60) as response:
        payload = json.load(response)
    rows: list[dict[str, str]] = []
    for binding in payload["results"]["bindings"]:
        rows.append(
            {
                "item": binding["item"]["value"],
                "sci": binding["sci"]["value"],
                "name": binding["name"]["value"],
                "lang": binding["lang"]["value"],
                "prop": binding["prop"]["value"],
            }
        )
    return rows


def build() -> dict:
    by_slug = {species.slug: species for species in SPECIES}
    chosen: dict[tuple[str, str], dict[str, str]] = {}
    for row in _query():
        slug = WIKIDATA_SCIENTIFIC_TO_SLUG.get(row["sci"])
        species = by_slug.get(slug or "")
        if species is None:
            continue
        locale = accept_wikidata_name(
            slug=species.slug,
            scientific_name=species.scientific_name,
            name=row["name"],
            lang=row["lang"],
        )
        if locale is None or locale == "en-GB":
            continue
        candidate = {
            "slug": species.slug,
            "locale": locale,
            "name": row["name"].strip(),
            "source": "wikidata",
            "source_property": row["prop"],
                "source_url": row["item"].replace("http://www.wikidata.org/entity/", "https://www.wikidata.org/wiki/"),
            "lang": row["lang"].lower(),
            "verification_status": "VERIFIED",
        }
        key = (species.slug, locale)
        chosen[key] = prefer_candidate(chosen.get(key), candidate)
    records = []
    for species in SPECIES:
        records.append(
            {
                "slug": species.slug,
                "locale": "en-GB",
                "name": species.common_name,
                "source": "biowiki_paleogenomics_catalogue",
                "source_property": "curated_english_vernacular",
                "source_url": f"https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id={species.tax_id}",
                "verification_status": "VERIFIED",
            }
        )
    for item in chosen.values():
        item.pop("lang", None)
        records.append(item)
    records.sort(key=lambda row: (row["slug"], row["locale"]))
    return {
        "retrieved_on": date.today().isoformat(),
        "note": (
            "English names are the curated BioWiki paleogenomics vernacular, "
            "cited to the NCBI Taxonomy record. Other locales come from Wikidata "
            "P1843 or rdfs:label after rejection of scientific names and known "
            "mis-associations. Missing languages are omitted on purpose."
        ),
        "records": records,
    }


def main() -> int:
    payload = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(payload['records'])} vernacular rows to {OUT.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
