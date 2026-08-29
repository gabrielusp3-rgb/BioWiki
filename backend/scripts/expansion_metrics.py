"""Database-derived biodiversity metrics for a catalogue expansion.

Never fabricates counts. Run against the live session:

    python -m scripts.expansion_metrics
    python -m scripts.expansion_metrics --json data/expansion_metrics.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import func, select

from app.core.stdio import configure_utf8_stdio
from app.database.session import get_sessionmaker
from app.models.enums import CrisprEvidenceType, SequenceType
from app.models.features import CrisprFeature, RnaFeature, VirusFeature
from app.models.genome import GenomeRecord
from app.models.organism import Organism
from app.models.publication import Publication, SequenceReference
from app.models.sequence import Sequence
from app.models.source import DataSource

configure_utf8_stdio()


def _shannon(counts: list[int]) -> float | None:
    total = sum(counts)
    if total <= 0:
        return None
    entropy = 0.0
    for n in counts:
        if n <= 0:
            continue
        p = n / total
        entropy -= p * math.log(p)
    return round(entropy, 4)


def _genus(name: str | None) -> str | None:
    if not name:
        return None
    token = name.strip().split()[0] if name.strip() else ""
    return token or None


def _family_from_lineage(lineage: list[str] | None) -> str | None:
    if not lineage:
        return None
    for item in reversed(lineage):
        text = str(item).strip()
        if text.endswith("dae") and " " not in text:
            return text
    return None


async def collect_metrics() -> dict[str, Any]:
    async with get_sessionmaker()() as session:
        sequences = int((await session.execute(select(func.count(Sequence.id)))).scalar_one())
        by_type = {
            (st.value if hasattr(st, "value") else str(st)): int(n)
            for st, n in (
                await session.execute(
                    select(Sequence.seq_type, func.count(Sequence.id)).group_by(Sequence.seq_type)
                )
            ).all()
        }
        by_source = {
            str(key): int(n)
            for key, n in (
                await session.execute(
                    select(DataSource.key, func.count(Sequence.id))
                    .join(Sequence, Sequence.source_id == DataSource.id)
                    .group_by(DataSource.key)
                )
            ).all()
        }
        by_group = {
            (g.value if hasattr(g, "value") else str(g)): int(n)
            for g, n in (
                await session.execute(
                    select(Organism.group, func.count(Organism.id)).group_by(Organism.group)
                )
            ).all()
        }
        organisms = list(
            (await session.execute(select(Organism))).scalars().all()
        )
        tax_rows = (
            await session.execute(
                select(Organism.tax_id, Organism.scientific_name, func.count(Sequence.id))
                .join(Sequence, Sequence.organism_id == Organism.id)
                .group_by(Organism.tax_id, Organism.scientific_name)
                .order_by(func.count(Sequence.id).desc())
            )
        ).all()
        type_tax = (
            await session.execute(
                select(
                    Sequence.seq_type,
                    Organism.scientific_name,
                    func.count(Sequence.id),
                )
                .join(Organism, Sequence.organism_id == Organism.id)
                .group_by(Sequence.seq_type, Organism.scientific_name)
            )
        ).all()
        rna_classes = {
            (rc.value if hasattr(rc, "value") else str(rc)): int(n)
            for rc, n in (
                await session.execute(
                    select(RnaFeature.rna_class, func.count(RnaFeature.sequence_id)).group_by(
                        RnaFeature.rna_class
                    )
                )
            ).all()
        }
        virus_genomes = {
            (gt.value if hasattr(gt, "value") else str(gt)): int(n)
            for gt, n in (
                await session.execute(
                    select(VirusFeature.genome_type, func.count(VirusFeature.sequence_id)).group_by(
                        VirusFeature.genome_type
                    )
                )
            ).all()
        }
        crispr_ev = {
            (ev.value if hasattr(ev, "value") else str(ev)): int(n)
            for ev, n in (
                await session.execute(
                    select(
                        CrisprFeature.evidence_type, func.count(CrisprFeature.sequence_id)
                    ).group_by(CrisprFeature.evidence_type)
                )
            ).all()
        }
        cas_systems = {
            (cs.value if hasattr(cs, "value") else str(cs)): int(n)
            for cs, n in (
                await session.execute(
                    select(CrisprFeature.cas_system, func.count(CrisprFeature.sequence_id)).group_by(
                        CrisprFeature.cas_system
                    )
                )
            ).all()
        }
        crispr_orgs = (
            await session.execute(
                select(
                    CrisprFeature.evidence_type,
                    Organism.scientific_name,
                    Organism.group,
                    Organism.tax_id,
                    func.count(Sequence.id),
                )
                .join(Sequence, Sequence.id == CrisprFeature.sequence_id)
                .join(Organism, Sequence.organism_id == Organism.id)
                .group_by(
                    CrisprFeature.evidence_type,
                    Organism.scientific_name,
                    Organism.group,
                    Organism.tax_id,
                )
            )
        ).all()
        residues = int(
            (await session.execute(select(func.coalesce(func.sum(Sequence.length), 0)))).scalar_one()
        )
        publications = int((await session.execute(select(func.count(Publication.id)))).scalar_one())
        unique_pmids = int(
            (
                await session.execute(
                    select(func.count(func.distinct(Publication.pubmed_id))).where(
                        Publication.pubmed_id.is_not(None)
                    )
                )
            ).scalar_one()
        )
        linked = int(
            (
                await session.execute(
                    select(func.count(func.distinct(SequenceReference.publication_id)))
                )
            ).scalar_one()
        )
        genomes = int((await session.execute(select(func.count(GenomeRecord.id)))).scalar_one())
        genome_seq = int(
            (
                await session.execute(
                    select(func.count(Sequence.id)).where(Sequence.seq_type == SequenceType.GENOME)
                )
            ).scalar_one()
        )
        dup_keys = (
            await session.execute(
                select(Sequence.accession, Sequence.source_id, Sequence.version)
                .group_by(Sequence.accession, Sequence.source_id, Sequence.version)
                .having(func.count() > 1)
            )
        ).all()

    species_counts = [(int(tid), name, int(n)) for tid, name, n in tax_rows]
    genera = Counter()
    families = Counter()
    for org in organisms:
        g = _genus(org.scientific_name)
        if g:
            genera[g] += 1
        fam = _family_from_lineage(list(org.lineage or []))
        if fam:
            families[fam] += 1

    top_by_type: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for st, name, n in type_tax:
        key = st.value if hasattr(st, "value") else str(st)
        top_by_type[key].append({"organism": name, "records": int(n)})
    for key, rows in top_by_type.items():
        rows.sort(key=lambda row: row["records"], reverse=True)
        top_by_type[key] = rows[:25]

    natural_taxa = {
        name for ev, name, _group, _tid, _n in crispr_orgs if ev == CrisprEvidenceType.NATURAL_CRISPR_ELEMENT
    }
    experimental_taxa = {
        name for ev, name, _group, _tid, _n in crispr_orgs if ev == CrisprEvidenceType.EXPERIMENTAL_GUIDE
    }
    computational_taxa = {
        name
        for ev, name, _group, _tid, _n in crispr_orgs
        if ev == CrisprEvidenceType.COMPUTATIONAL_TARGET
    }
    natural_groups = Counter()
    for ev, _name, group, _tid, n in crispr_orgs:
        if ev == CrisprEvidenceType.NATURAL_CRISPR_ELEMENT:
            label = group.value if hasattr(group, "value") else str(group)
            natural_groups[label] += int(n)

    record_counts = [n for _tid, _name, n in species_counts]
    return {
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "sequences": sequences,
        "by_type": by_type,
        "by_source": by_source,
        "residues": residues,
        "organisms": len(organisms),
        "unique_tax_ids": len({org.tax_id for org in organisms}),
        "organism_groups": by_group,
        "unique_genera": len(genera),
        "unique_families_from_lineage": len(families),
        "shannon_species_records": _shannon(record_counts),
        "top_25_species": [
            {"tax_id": tid, "organism": name, "records": n} for tid, name, n in species_counts[:25]
        ],
        "top_25_by_type": dict(top_by_type),
        "rna_classes": rna_classes,
        "virus_genome_types": virus_genomes,
        "crispr": {
            "by_evidence": crispr_ev,
            "cas_systems": cas_systems,
            "natural_taxa": sorted(natural_taxa),
            "experimental_taxa": sorted(experimental_taxa),
            "computational_taxa": sorted(computational_taxa),
            "natural_group_records": dict(natural_groups),
        },
        "genomes": genomes,
        "unintended_genome_sequences": genome_seq,
        "publications": publications,
        "unique_pmids": unique_pmids,
        "linked_publications": linked,
        "standalone_publications": publications - linked,
        "duplicate_natural_keys": len(dup_keys),
        "notes": [
            "Shannon index is on catalogue record counts per species, not a field biodiversity score.",
            "Family counts use lineage names ending in -dae when present.",
        ],
    }


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", type=Path, default=None)
    args = parser.parse_args()
    metrics = await collect_metrics()
    text = json.dumps(metrics, indent=2, default=str)
    print(text)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    asyncio.run(main())
