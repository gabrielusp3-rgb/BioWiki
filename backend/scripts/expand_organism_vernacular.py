"""Add verified vernacular names for catalogue organisms. Never invents a name.

English uses the stored organism.common_name when it is not the binomial.
Other locales come from Wikidata P1843 via the NCBI TaxID (P685).
Rows curated as biowiki_paleogenomics_catalogue are left unchanged.
"""

from __future__ import annotations

import asyncio
import json
import sys
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from sqlalchemy import select

from app.database.session import get_sessionmaker
from app.models.organism import Organism
from app.models.vernacular import OrganismVernacularName
from app.pipeline.paleogenomics.vernacular import (
    LOCALES,
    accept_wikidata_name,
    looks_like_scientific_name,
)

LANGS = ("pt", "pt-br", "en", "es", "de", "it", "zh", "zh-hans", "ja", "ar", "fr", "ru", "hi")
CHUNK = 40


def _wikidata(tax_ids: list[int], *, labels: bool) -> list[dict[str, str]]:
    values = " ".join(f'"{tax_id}"' for tax_id in tax_ids)
    lang_filter = ", ".join(f'"{lang}"' for lang in LANGS)
    sparql = f"""
SELECT ?tax ?item ?name ?lang WHERE {{
  VALUES ?tax {{ {values} }}
  ?item wdt:P685 ?tax .
  {"?item rdfs:label ?name ." if labels else "?item wdt:P1843 ?name ."}
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
    with urlopen(request, timeout=90) as response:
        payload = json.load(response)
    rows = []
    for binding in payload["results"]["bindings"]:
        rows.append(
            {
                "tax": binding["tax"]["value"],
                "item": binding["item"]["value"].replace(
                    "http://www.wikidata.org/entity/", "https://www.wikidata.org/wiki/"
                ),
                "name": binding["name"]["value"].strip(),
                "lang": binding["lang"]["value"],
            }
        )
    return rows


async def main() -> int:
    async with get_sessionmaker()() as session:
        organisms = (
            await session.execute(
                select(Organism.id, Organism.tax_id, Organism.scientific_name, Organism.common_name, Organism.slug)
            )
        ).all()
        existing = (
            await session.execute(
                select(
                    OrganismVernacularName.organism_id,
                    OrganismVernacularName.locale,
                    OrganismVernacularName.source,
                )
            )
        ).all()
    protected = {
        (row[0], row[1])
        for row in existing
        if row[2] == "biowiki_paleogenomics_catalogue"
    }
    have = {(row[0], row[1]) for row in existing}
    by_tax = {int(row.tax_id): row for row in organisms}
    inserted = skipped_protected = rejected = 0
    pending: list[OrganismVernacularName] = []

    for row in organisms:
        name = (row.common_name or "").strip()
        if not name or looks_like_scientific_name(name, row.scientific_name):
            continue
        key = (row.id, "en-GB")
        if key in protected or key in have:
            continue
        pending.append(
            OrganismVernacularName(
                organism_id=row.id,
                locale="en-GB",
                name=name[:300],
                source="organism.common_name",
                source_url=f"https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id={row.tax_id}",
                verification_status="VERIFIED",
            )
        )
        have.add(key)

    tax_ids = [int(row.tax_id) for row in organisms]
    remote: dict[tuple[int, str], dict[str, str]] = {}
    for start in range(0, len(tax_ids), CHUNK):
        chunk = tax_ids[start : start + CHUNK]
        print(f"wikidata {start + 1}-{start + len(chunk)} / {len(tax_ids)}", flush=True)
        try:
            hits = _wikidata(chunk, labels="--labels" in sys.argv)
        except Exception as exc:
            print(f"wikidata chunk failed: {type(exc).__name__}", flush=True)
            continue
        for hit in hits:
            try:
                tax_id = int(hit["tax"])
            except ValueError:
                continue
            organism = by_tax.get(tax_id)
            if organism is None:
                continue
            locale = accept_wikidata_name(
                slug=organism.slug,
                scientific_name=organism.scientific_name,
                name=hit["name"],
                lang=hit["lang"],
            )
            if locale is None or locale not in LOCALES:
                rejected += 1
                continue
            remote[(tax_id, locale)] = hit

    for (tax_id, locale), hit in remote.items():
        organism = by_tax[tax_id]
        key = (organism.id, locale)
        if key in protected or key in have:
            if key in protected:
                skipped_protected += 1
            continue
        pending.append(
            OrganismVernacularName(
                organism_id=organism.id,
                locale=locale,
                name=hit["name"][:300],
                source="wikidata",
                source_url=hit["item"][:500],
                verification_status="VERIFIED",
            )
        )
        have.add(key)

    async with get_sessionmaker()() as session:
        async with session.begin():
            session.add_all(pending)
            inserted = len(pending)
    print(json.dumps({"inserted": inserted, "rejected": rejected, "protected_kept": skipped_protected}))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
