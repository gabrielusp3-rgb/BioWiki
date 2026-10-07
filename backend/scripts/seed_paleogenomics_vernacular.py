"""Upsert verified Paleogenomics vernacular names. Does not create organisms or sequences."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from sqlalchemy import select

from app.database.session import get_sessionmaker
from app.models.organism import Organism
from app.models.paleogenomics import PaleogenomicProfile
from app.models.vernacular import OrganismVernacularName
from app.pipeline.paleogenomics.vernacular import LOCALES

DATA = Path(__file__).resolve().parents[1] / "app" / "data" / "paleogenomics_vernacular.json"


async def main() -> int:
    payload = json.loads(DATA.read_text(encoding="utf-8"))
    records = payload["records"]
    async with get_sessionmaker()() as session:
        async with session.begin():
            profiles = (
                await session.execute(
                    select(PaleogenomicProfile.slug, PaleogenomicProfile.organism_id)
                )
            ).all()
            organism_by_slug = {slug: organism_id for slug, organism_id in profiles}
            inserted = updated = skipped = 0
            for record in records:
                if record["locale"] not in LOCALES:
                    skipped += 1
                    continue
                organism_id = organism_by_slug.get(record["slug"])
                if organism_id is None:
                    organism_id = (
                        await session.execute(
                            select(Organism.id).where(Organism.slug == record["slug"])
                        )
                    ).scalar_one_or_none()
                if organism_id is None:
                    skipped += 1
                    continue
                existing = (
                    await session.execute(
                        select(OrganismVernacularName).where(
                            OrganismVernacularName.organism_id == organism_id,
                            OrganismVernacularName.locale == record["locale"],
                        )
                    )
                ).scalar_one_or_none()
                if existing is None:
                    session.add(
                        OrganismVernacularName(
                            organism_id=organism_id,
                            locale=record["locale"],
                            name=record["name"],
                            source=record["source"],
                            source_url=record.get("source_url"),
                            verification_status=record["verification_status"],
                        )
                    )
                    inserted += 1
                else:
                    existing.name = record["name"]
                    existing.source = record["source"]
                    existing.source_url = record.get("source_url")
                    existing.verification_status = record["verification_status"]
                    updated += 1
    print(json.dumps({"inserted": inserted, "updated": updated, "skipped": skipped}))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
