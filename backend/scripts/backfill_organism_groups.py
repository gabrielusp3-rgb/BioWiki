"""Reclassify organisms from official NCBI Taxonomy. Never invents a kingdom.

The importer used to persist ``OrganismGroup.BACTERIA`` when lineage was
missing. That stored sperm whale, pig, rat, a brassica and *Plasmodium* as
bacteria. This script fills lineage from NCBI Taxonomy XML and sets ``group``
from that lineage (division only as a last unambiguous resort).

Dry-run by default. From ``backend/``:

    python -m scripts.backfill_organism_groups
    python -m scripts.backfill_organism_groups --apply
"""

from __future__ import annotations

import argparse
import asyncio
import json
from dataclasses import dataclass, field

from sqlalchemy import func, select

from app.database.session import get_sessionmaker
from app.models.enums import OrganismGroup
from app.models.organism import Organism
from app.pipeline.fetchers.base import chunked
from app.pipeline.logging import get_logger
from app.pipeline.taxonomy import group_from_taxonomy, parse_ncbi_taxonomy_xml
from app.services.connectors.ncbi import NCBIConnector

logger = get_logger("biowiki.pipeline.backfill_organisms")


@dataclass
class OrganismFix:
    tax_id: int
    scientific_name: str
    before_group: str
    after_group: str
    before_lineage: list[str]
    after_lineage: list[str]
    status: str  # CORRECTED | LINEAGE_FILLED | UNCHANGED | TEMPORARILY_UNVERIFIED | SKIPPED


@dataclass
class BackfillReport:
    examined: int = 0
    fixes: list[OrganismFix] = field(default_factory=list)

    def as_dict(self) -> dict:
        counts: dict[str, int] = {}
        for item in self.fixes:
            counts[item.status] = counts.get(item.status, 0) + 1
        return {
            "examined": self.examined,
            "by_status": counts,
            "changes": [
                {
                    "tax_id": item.tax_id,
                    "scientific_name": item.scientific_name,
                    "before_group": item.before_group,
                    "after_group": item.after_group,
                    "status": item.status,
                    "lineage": item.after_lineage,
                }
                for item in self.fixes
                if item.status in {"CORRECTED", "LINEAGE_FILLED"}
            ],
            "temporarily_unverified": [
                item.tax_id for item in self.fixes if item.status == "TEMPORARILY_UNVERIFIED"
            ],
        }


async def _fetch_taxonomy(tax_ids: list[int]) -> dict[int, dict]:
    lookup: dict[int, dict] = {}
    async with NCBIConnector() as conn:
        for group in chunked([str(t) for t in tax_ids], 40):
            try:
                xml = await conn.efetch("taxonomy", list(group), rettype="xml", retmode="xml")
                lookup.update(parse_ncbi_taxonomy_xml(xml))
            except Exception:
                logger.exception("taxonomy efetch failed for %s", group)
    return lookup


async def backfill_organism_groups(*, apply: bool = False) -> BackfillReport:
    report = BackfillReport()
    session_factory = get_sessionmaker()

    async with session_factory() as session:
        rows = list(
            (
                await session.execute(
                    select(Organism).where(
                        func.coalesce(func.cardinality(Organism.lineage), 0) == 0
                    )
                )
            )
            .scalars()
            .all()
        )
        report.examined = len(rows)
        tax_ids = [int(row.tax_id) for row in rows]
        lookup = await _fetch_taxonomy(tax_ids) if tax_ids else {}

        for row in rows:
            before_group = row.group.value if row.group else ""
            before_lineage = list(row.lineage or [])
            doc = lookup.get(int(row.tax_id))
            if not doc:
                report.fixes.append(
                    OrganismFix(
                        tax_id=int(row.tax_id),
                        scientific_name=row.scientific_name,
                        before_group=before_group,
                        after_group=before_group,
                        before_lineage=before_lineage,
                        after_lineage=before_lineage,
                        status="TEMPORARILY_UNVERIFIED",
                    )
                )
                continue

            lineage = list(doc.get("lineage") or [])
            group = group_from_taxonomy(lineage=lineage, division=doc.get("division"))
            if not group:
                report.fixes.append(
                    OrganismFix(
                        tax_id=int(row.tax_id),
                        scientific_name=row.scientific_name,
                        before_group=before_group,
                        after_group=before_group,
                        before_lineage=before_lineage,
                        after_lineage=lineage or before_lineage,
                        status="SKIPPED",
                    )
                )
                continue

            status = "UNCHANGED"
            if group != before_group:
                status = "CORRECTED"
            elif lineage and lineage != before_lineage:
                status = "LINEAGE_FILLED"

            if apply and status in {"CORRECTED", "LINEAGE_FILLED"}:
                row.group = OrganismGroup(group)
                if lineage:
                    row.lineage = lineage
                if doc.get("rank") and not row.rank:
                    row.rank = str(doc["rank"])[:64]
                if doc.get("common_name") and not row.common_name:
                    row.common_name = str(doc["common_name"])[:300]

            report.fixes.append(
                OrganismFix(
                    tax_id=int(row.tax_id),
                    scientific_name=row.scientific_name,
                    before_group=before_group,
                    after_group=group,
                    before_lineage=before_lineage,
                    after_lineage=lineage or before_lineage,
                    status=status,
                )
            )

        if apply:
            await session.commit()
        else:
            await session.rollback()

    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write lineage and group. Default is a dry-run (rollback).",
    )
    args = parser.parse_args()
    report = asyncio.run(backfill_organism_groups(apply=args.apply))
    print(json.dumps(report.as_dict(), indent=2, default=str))
    if not args.apply:
        print("dry-run: no rows written; re-run with --apply to persist")


if __name__ == "__main__":
    main()
