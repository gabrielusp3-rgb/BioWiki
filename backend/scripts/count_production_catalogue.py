"""Read-only production catalogue counts. Never writes."""

from __future__ import annotations

import asyncio
import json

from sqlalchemy import func, select, text

from app.database.session import get_sessionmaker
from app.models.genome import GenomeRecord
from app.models.organism import Organism
from app.models.publication import Publication
from app.models.sequence import Sequence


async def main() -> None:
    async with get_sessionmaker()() as session:
        seq_by_type = {
            str(row[0]): int(row[1])
            for row in (
                await session.execute(
                    select(Sequence.seq_type, func.count()).group_by(Sequence.seq_type)
                )
            ).all()
        }
        revision = (
            await session.execute(text("SELECT version_num FROM alembic_version"))
        ).scalar_one_or_none()
        tables = [
            row[0]
            for row in (
                await session.execute(
                    text(
                        """
                        SELECT tablename FROM pg_tables
                        WHERE schemaname = 'public'
                          AND tablename LIKE 'paleogenomic%'
                        ORDER BY 1
                        """
                    )
                )
            ).all()
        ]
        payload = {
            "alembic_revision": revision,
            "sequences": int(
                (await session.execute(select(func.count()).select_from(Sequence))).scalar_one()
            ),
            "seq_by_type": seq_by_type,
            "organisms": int(
                (await session.execute(select(func.count()).select_from(Organism))).scalar_one()
            ),
            "genome_records": int(
                (await session.execute(select(func.count()).select_from(GenomeRecord))).scalar_one()
            ),
            "publications": int(
                (await session.execute(select(func.count()).select_from(Publication))).scalar_one()
            ),
            "unique_pmids": int(
                (
                    await session.execute(
                        select(func.count(func.distinct(Publication.pubmed_id))).where(
                            Publication.pubmed_id.is_not(None)
                        )
                    )
                ).scalar_one()
            ),
            "paleogenomic_tables": tables,
        }
    print(json.dumps(payload, indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(main())
