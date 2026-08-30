"""Print Paleogenomics and catalogue counts from the connected database. No secrets."""

from __future__ import annotations

import asyncio
import json
from collections import defaultdict

from sqlalchemy import func, select, text

from app.database.session import get_sessionmaker
from app.models.organism import Organism
from app.models.paleogenomics import (
    PaleogenomicIntrogressionRegion,
    PaleogenomicProfile,
    PaleogenomicProject,
    PaleogenomicPublicationMembership,
    PaleogenomicSequenceMembership,
)
from app.models.publication import Publication
from app.models.sequence import Sequence
from app.models.genome import GenomeRecord
from app.pipeline.paleogenomics.catalogue import SPECIES
from app.services import sync_service


async def main() -> None:
    async with get_sessionmaker()() as session:
        integrity = await sync_service.check_integrity(session)
        seq_by_type = {
            str(row[0]): int(row[1])
            for row in (
                await session.execute(
                    select(Sequence.seq_type, func.count()).group_by(Sequence.seq_type)
                )
            ).all()
        }
        pmids = int(
            (
                await session.execute(
                    select(func.count(func.distinct(Publication.pubmed_id))).where(
                        Publication.pubmed_id.is_not(None)
                    )
                )
            ).scalar_one()
        )
        natural_dupes = (
            await session.execute(
                text(
                    """
                    SELECT source_id, accession, version, COUNT(*) AS n
                    FROM sequences
                    GROUP BY 1, 2, 3
                    HAVING COUNT(*) > 1
                    LIMIT 20
                    """
                )
            )
        ).all()
        pmid_dupes = (
            await session.execute(
                text(
                    """
                    SELECT pubmed_id, COUNT(*) AS n
                    FROM publications
                    WHERE pubmed_id IS NOT NULL
                    GROUP BY pubmed_id
                    HAVING COUNT(*) > 1
                    LIMIT 20
                    """
                )
            )
        ).all()
        doi_dupes = (
            await session.execute(
                text(
                    """
                    SELECT lower(doi), COUNT(*) AS n
                    FROM publications
                    WHERE doi IS NOT NULL AND btrim(doi) <> ''
                    GROUP BY lower(doi)
                    HAVING COUNT(*) > 1
                    LIMIT 20
                    """
                )
            )
        ).all()
        tax_dupes = (
            await session.execute(
                text(
                    """
                    SELECT tax_id, COUNT(*) AS n
                    FROM organisms
                    GROUP BY tax_id
                    HAVING COUNT(*) > 1
                    LIMIT 20
                    """
                )
            )
        ).all()
        species_rows = []
        for species in SPECIES:
            profile = (
                await session.execute(
                    select(PaleogenomicProfile).where(PaleogenomicProfile.slug == species.slug)
                )
            ).scalar_one_or_none()
            if profile is None:
                species_rows.append({"slug": species.slug, "missing_profile": True})
                continue
            seq_n = int(
                (
                    await session.execute(
                        select(func.count()).where(
                            PaleogenomicSequenceMembership.profile_id == profile.id
                        )
                    )
                ).scalar_one()
            )
            pub_n = int(
                (
                    await session.execute(
                        select(func.count()).where(
                            PaleogenomicPublicationMembership.profile_id == profile.id
                        )
                    )
                ).scalar_one()
            )
            proj_n = int(
                (
                    await session.execute(
                        select(func.count()).where(PaleogenomicProject.profile_id == profile.id)
                    )
                ).scalar_one()
            )
            asm_n = int(
                (
                    await session.execute(
                        select(func.count()).where(GenomeRecord.organism_id == profile.organism_id)
                    )
                ).scalar_one()
            )
            mt_n = int(
                (
                    await session.execute(
                        select(func.count()).where(
                            PaleogenomicSequenceMembership.profile_id == profile.id,
                            PaleogenomicSequenceMembership.is_complete_mitogenome.is_(True),
                        )
                    )
                ).scalar_one()
            )
            kinds = defaultdict(int)
            for kind, n in (
                await session.execute(
                    select(PaleogenomicSequenceMembership.record_kind, func.count())
                    .where(PaleogenomicSequenceMembership.profile_id == profile.id)
                    .group_by(PaleogenomicSequenceMembership.record_kind)
                )
            ).all():
                kinds[str(kind)] = int(n)
            org = (
                await session.execute(select(Organism).where(Organism.id == profile.organism_id))
            ).scalar_one()
            species_rows.append(
                {
                    "slug": species.slug,
                    "scientific_name": org.scientific_name,
                    "tax_id": org.tax_id,
                    "target": species.preferred_sequence_target,
                    "sequences": seq_n,
                    "mitogenomes": mt_n,
                    "assemblies": asm_n,
                    "projects": proj_n,
                    "publications": pub_n,
                    "kinds": dict(kinds),
                    "extinction_status": org.extinction_status,
                }
            )
        payload = {
            "integrity_ok": integrity.ok if hasattr(integrity, "ok") else None,
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
            "unique_pmids": pmids,
            "paleogenomic_sequences": int(
                (
                    await session.execute(
                        select(func.count()).select_from(PaleogenomicSequenceMembership)
                    )
                ).scalar_one()
            ),
            "paleogenomic_profiles": int(
                (
                    await session.execute(select(func.count()).select_from(PaleogenomicProfile))
                ).scalar_one()
            ),
            "introgression": int(
                (
                    await session.execute(
                        select(func.count()).select_from(PaleogenomicIntrogressionRegion)
                    )
                ).scalar_one()
            ),
            "paleogenomic_projects": int(
                (
                    await session.execute(select(func.count()).select_from(PaleogenomicProject))
                ).scalar_one()
            ),
            "paleogenomic_publication_links": int(
                (
                    await session.execute(
                        select(func.count()).select_from(PaleogenomicPublicationMembership)
                    )
                ).scalar_one()
            ),
            "duplicate_natural_keys": [dict(row._mapping) for row in natural_dupes],
            "duplicate_pmids": [dict(row._mapping) for row in pmid_dupes],
            "duplicate_dois": [dict(row._mapping) for row in doi_dupes],
            "duplicate_tax_ids": [dict(row._mapping) for row in tax_dupes],
            "species": species_rows,
        }
        if hasattr(integrity, "model_dump"):
            payload["integrity"] = integrity.model_dump(by_alias=True, mode="json")
    print(json.dumps(payload, indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(main())
