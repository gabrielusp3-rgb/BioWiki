"""Post-expansion checks against the live PostgreSQL database and search layer."""

from __future__ import annotations

import asyncio
import json
import time
from collections import Counter

from sqlalchemy import func, select, text

from app.database.session import get_sessionmaker
from app.models.organism import Organism
from app.models.publication import Publication
from app.models.sequence import Sequence
from app.models.source import DataSource
from app.services import search_service, sync_service
from scripts.expand_dataset import snapshot


async def main() -> None:
    stats = await snapshot()
    print(json.dumps(stats, indent=2, default=str))

    async with get_sessionmaker()() as session:
        integrity = await sync_service.check_integrity(session)
        print("integrity", integrity.ok)
        refreshed = await sync_service.refresh_counts(session)
        print("refreshed", refreshed)

        samples = {
            "accession": (
                await session.execute(select(Sequence.accession).limit(1))
            ).scalar_one(),
            "gene": (
                await session.execute(
                    select(Sequence.gene_name)
                    .where(Sequence.gene_name.is_not(None))
                    .limit(1)
                )
            ).scalar_one(),
            "organism": (
                await session.execute(select(Organism.scientific_name).limit(1))
            ).scalar_one(),
            "pmid": (
                await session.execute(
                    select(Publication.pubmed_id)
                    .where(Publication.pubmed_id.is_not(None))
                    .limit(1)
                )
            ).scalar_one(),
            "protein": (
                await session.execute(
                    select(Sequence.accession).where(Sequence.seq_type == "protein").limit(1)
                )
            ).scalar_one(),
        }
        print("samples", samples)

        queries = [
            samples["accession"],
            samples["gene"],
            samples["organism"],
            "CRISPR",
            "virus",
            "dna",
            "rna",
            "genoma" if False else "genome",
            "bacteria",
        ]
        for q in queries:
            t0 = time.perf_counter()
            result = await search_service.search(session, q=str(q), limit=5)
            dt = (time.perf_counter() - t0) * 1000
            print(f"search {q!r}: total={result.get('total')} items={len(result.get('items') or [])} {dt:.0f}ms")

        page1 = await search_service.search(session, q="sapiens", limit=10)
        page2 = await search_service.search(
            session, q="sapiens", limit=10, cursor=page1.get("next_cursor")
        )
        ids1 = {item.get("accession") for item in page1.get("items") or []}
        ids2 = {item.get("accession") for item in page2.get("items") or []}
        print("pagination overlap", len(ids1 & ids2), "page1", len(ids1), "page2", len(ids2))

        has_vector = (
            await session.execute(
                text(
                    "SELECT COUNT(*) FROM information_schema.columns "
                    "WHERE table_name='sequences' AND column_name='search_vector'"
                )
            )
        ).scalar_one()
        print("search_vector column", bool(has_vector))

        top_orgs = (
            await session.execute(
                select(Organism.scientific_name, Organism.group, Organism.sequence_count)
                .order_by(Organism.sequence_count.desc().nullslast())
                .limit(8)
            )
        ).all()
        print("top organisms")
        for name, group, count in top_orgs:
            g = group.value if hasattr(group, "value") else group
            print(f"  {count:>5}  {g:<10} {name}")


if __name__ == "__main__":
    asyncio.run(main())
