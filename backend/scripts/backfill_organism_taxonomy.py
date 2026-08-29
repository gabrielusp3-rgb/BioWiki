"""Apply NCBI Taxonomy corrections for every stored organism.

Dry-run by default. Updates only when NCBI Taxonomy XML proves:

- a different canonical scientific name (not a listed synonym);
- a merged TaxID whose target is not already stored;
- missing or stale lineage;
- a group that disagrees with lineage.

Never invents ``bacteria``. From ``backend/``::

    python -m scripts.backfill_organism_taxonomy
    python -m scripts.backfill_organism_taxonomy --apply
"""

from __future__ import annotations

import argparse
import asyncio
import json

from sqlalchemy import select

from app.database.session import get_sessionmaker
from app.models.enums import OrganismGroup
from app.models.organism import Organism
from app.pipeline.fetchers.base import chunked
from app.pipeline.logging import get_logger
from app.pipeline.phase0.names import (
    MERGED_TAXID,
    UPDATED_CANONICAL_NAME,
    classify_organism_taxonomy,
)
from app.pipeline.taxonomy import group_from_taxonomy, index_taxonomy_for_requested
from app.services.connectors.ncbi import NCBIConnector

logger = get_logger("biowiki.pipeline.backfill_organism_taxonomy")


async def _fetch_taxonomy(tax_ids: list[int]) -> dict[int, dict]:
    lookup: dict[int, dict] = {}
    async with NCBIConnector() as conn:
        for group in chunked([str(t) for t in tax_ids], 40):
            try:
                xml = await conn.efetch("taxonomy", list(group), rettype="xml", retmode="xml")
                requested = [int(t) for t in group if str(t).isdigit()]
                lookup.update(index_taxonomy_for_requested(xml, requested))
            except Exception:
                logger.exception("taxonomy efetch failed for %s", group)
    return lookup


async def backfill(*, apply: bool = False) -> dict:
    session_factory = get_sessionmaker()
    changes: list[dict] = []
    async with session_factory() as session:
        rows = list((await session.execute(select(Organism))).scalars().all())
        occupied = {int(r.tax_id): r.id for r in rows}
        lookup = await _fetch_taxonomy([int(r.tax_id) for r in rows])
        for row in rows:
            doc = lookup.get(int(row.tax_id))
            classified = classify_organism_taxonomy(
                stored_tax_id=int(row.tax_id),
                stored_name=row.scientific_name,
                ncbi=doc,
            )
            if not doc:
                changes.append(
                    {
                        "tax_id": int(row.tax_id),
                        "scientific_name": row.scientific_name,
                        "status": "TEMPORARILY_UNVERIFIED",
                    }
                )
                continue
            lineage = list(doc.get("lineage") or [])
            group = group_from_taxonomy(lineage=lineage, division=doc.get("division"))
            actions: list[str] = [classified["status"]]
            if apply:
                if lineage and lineage != list(row.lineage or []):
                    row.lineage = lineage
                    actions.append("LINEAGE_UPDATED")
                if group and group != row.group.value:
                    row.group = OrganismGroup(group)
                    actions.append("GROUP_CORRECTED")
                if classified["status"] == UPDATED_CANONICAL_NAME and classified.get("canonical_name"):
                    row.scientific_name = str(classified["canonical_name"])[:300]
                    actions.append("NAME_UPDATED")
                if classified["status"] == MERGED_TAXID:
                    canonical = int(classified["canonical_tax_id"])
                    holder = occupied.get(canonical)
                    if holder is None or holder == row.id:
                        occupied.pop(int(row.tax_id), None)
                        row.tax_id = canonical
                        occupied[canonical] = row.id
                        actions.append("TAXID_MERGED")
                    else:
                        actions.append("TAXID_MERGE_BLOCKED_DUPLICATE")
                if doc.get("rank") and not row.rank:
                    row.rank = str(doc["rank"])[:64]
            changes.append(
                {
                    "tax_id": int(row.tax_id),
                    "scientific_name": row.scientific_name,
                    "canonical_tax_id": classified.get("canonical_tax_id"),
                    "canonical_name": classified.get("canonical_name"),
                    "ncbi_group": group,
                    "stored_group": row.group.value,
                    "actions": actions,
                }
            )
        if apply:
            await session.commit()
        else:
            await session.rollback()
    return {
        "examined": len(changes),
        "apply": apply,
        "changes": changes,
        "temporarily_unverified": [
            c["tax_id"] for c in changes if c.get("status") == "TEMPORARILY_UNVERIFIED"
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    report = asyncio.run(backfill(apply=args.apply))
    print(json.dumps(report, indent=2, default=str)[:20000])
    if not args.apply:
        print("dry-run: no rows written; re-run with --apply to persist")


if __name__ == "__main__":
    main()
