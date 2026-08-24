"""Initial population of BIOWIKI with real records from official sources.

Reproducible, idempotent (every importer upserts by accession) and honest:
every accession below is a real, curated identifier from NCBI GenBank/RefSeq,
UniProtKB or NCBI Datasets; term searches use documented Entrez syntax and
import whatever the source actually returns. Nothing is fabricated.

Run from ``backend/`` with the virtualenv active:

    python -m scripts.seed_initial              # full seed
    python -m scripts.seed_initial --no-search  # curated accessions only

The script finishes by backfilling PubMed metadata for every publication that
was created from partial GenBank REFERENCE blocks, refreshing per-organism
sequence counts and printing real per-category totals from the database.
"""

from __future__ import annotations

import argparse
import asyncio
from collections import Counter

from sqlalchemy import func, select

from app.database.session import get_sessionmaker
from app.models.organism import Organism
from app.models.publication import Publication, SequenceReference
from app.models.sequence import Sequence
from app.pipeline.fetchers import datasets, ncbi, pubmed, uniprot
from app.pipeline.models import ImportReport

# ---------------------------------------------------------------------------
# Curated real accessions (NCBI nuccore) — DNA / genomic records
# ---------------------------------------------------------------------------
DNA_ACCESSIONS = [
    # Human RefSeqGene regions (curated gene loci)
    "NG_017013",  # TP53 tumor suppressor gene region
    "NG_005905",  # BRCA1 gene region
    "NG_016465",  # CFTR gene region
    "NG_000007",  # beta-globin (HBB) gene cluster
    "NG_012232",  # DMD (dystrophin) gene region
    "NG_008847",  # MECP2 gene region
    "NG_009497",  # LDLR gene region
    # Classic GenBank genomic records
    "J01636",     # E. coli lactose operon (lacI-lacZYA)
    "V00565",     # Human preproinsulin gene
    "U49845",     # S. cerevisiae TCP1-beta (canonical NCBI sample record)
    "J01859",     # E. coli 16S ribosomal RNA gene
    "M13971",     # Human tissue plasminogen activator gene exon 1 region
]

# Genomic term searches (real Entrez syntax; size-bounded to avoid chromosomes)
DNA_SEARCHES = [
    ('Arabidopsis thaliana[Organism] AND biomol_genomic[PROP] AND '
     '"complete cds"[Title] AND 1000:30000[SLEN]', 15),
    ('Drosophila melanogaster[Organism] AND biomol_genomic[PROP] AND '
     '"complete cds"[Title] AND 1000:30000[SLEN]', 15),
    ('Escherichia coli[Organism] AND biomol_genomic[PROP] AND '
     '"complete cds"[Title] AND 1000:30000[SLEN]', 15),
    ('Saccharomyces cerevisiae[Organism] AND biomol_genomic[PROP] AND '
     '"complete cds"[Title] AND 1000:30000[SLEN]', 10),
]

# ---------------------------------------------------------------------------
# RNA — curated RefSeq mRNAs and ncRNAs plus per-organism mRNA searches
# ---------------------------------------------------------------------------
RNA_ACCESSIONS = [
    # Human mRNA (RefSeq curated)
    "NM_000546",  # TP53
    "NM_007294",  # BRCA1
    "NM_000518",  # HBB
    "NM_000207",  # INS
    "NM_004333",  # BRAF
    "NM_005228",  # EGFR
    "NM_000492",  # CFTR
    "NM_002046",  # GAPDH
    "NM_001101",  # ACTB
    "NM_000059",  # BRCA2
    # Mouse mRNA
    "NM_011640",  # Trp53
    "NM_008084",  # Gapdh
    "NM_007393",  # Actb
    # Human non-coding RNA
    "NR_003286",  # RNA18SN5 (18S ribosomal RNA)
    "NR_002819",  # MALAT1 lncRNA
    "NR_046018",  # DDX11L1
    "NR_001566",  # TERC (telomerase RNA component)
    # Classic GenBank mRNA
    "M10051",     # Human insulin receptor mRNA
]

RNA_SEARCHES = [
    ('Danio rerio[Organism] AND biomol_mrna[PROP] AND refseq[filter] AND '
     '500:15000[SLEN]', 12),
    ('Drosophila melanogaster[Organism] AND biomol_mrna[PROP] AND refseq[filter] AND '
     '500:15000[SLEN]', 12),
    ('Arabidopsis thaliana[Organism] AND biomol_mrna[PROP] AND refseq[filter] AND '
     '500:15000[SLEN]', 12),
    ('Saccharomyces cerevisiae[Organism] AND biomol_mrna[PROP] AND refseq[filter] AND '
     '500:15000[SLEN]', 12),
    ('Caenorhabditis elegans[Organism] AND biomol_mrna[PROP] AND refseq[filter] AND '
     '500:15000[SLEN]', 12),
    # Bacterial/archaeal 16S rRNA (RefSeq targeted loci records)
    ('"16S ribosomal RNA"[Title] AND refseq[filter] AND 1200:1800[SLEN]', 15),
]

# ---------------------------------------------------------------------------
# Proteins — curated UniProtKB accessions (all real, mostly Swiss-Prot)
# ---------------------------------------------------------------------------
PROTEIN_ACCESSIONS = [
    # Human
    "P04637",  # Cellular tumor antigen p53
    "P01308",  # Insulin
    "P68871",  # Hemoglobin subunit beta
    "P69905",  # Hemoglobin subunit alpha
    "P02144",  # Myoglobin
    "P00533",  # EGFR
    "P38398",  # BRCA1
    "P05067",  # Amyloid-beta precursor protein
    "P04156",  # Major prion protein
    "P01112",  # HRAS
    "P01116",  # KRAS
    "P04626",  # ERBB2 (HER2)
    "P06213",  # Insulin receptor
    "P02649",  # Apolipoprotein E
    "P00734",  # Prothrombin
    "Q8WZ42",  # Titin
    # Other animals
    "P02340",  # p53 (mouse)
    "P00698",  # Lysozyme C (chicken)
    "P02769",  # Serum albumin (bovine)
    "P00760",  # Trypsin (bovine)
    # Fluorescent / model proteins
    "P42212",  # Green fluorescent protein (Aequorea victoria)
    # Fungi
    "P00330",  # Alcohol dehydrogenase 1 (S. cerevisiae)
    # Bacteria
    "P0A7G6",  # RecA (E. coli)
    "Q99ZW2",  # Cas9 (Streptococcus pyogenes) — CRISPR effector
    "A0Q7Q2",  # Cas12a (Francisella tularensis) — CRISPR effector
    # Viruses
    "P0DTC2",  # Spike glycoprotein (SARS-CoV-2)
    "P0DTC9",  # Nucleoprotein (SARS-CoV-2)
    "P03452",  # Hemagglutinin (Influenza A/PR/8/34)
]

# ---------------------------------------------------------------------------
# CRISPR — real CRISPR loci (arrays/repeat regions) sequenced from organisms
# ---------------------------------------------------------------------------
CRISPR_SEARCHES = [
    ('CRISPR[Title] AND (array[Title] OR "repeat region"[Title] OR locus[Title]) '
     'AND 100:50000[SLEN]', 30),
]

# ---------------------------------------------------------------------------
# Viruses — complete genomes (RefSeq) with ICTV families in their lineage
# ---------------------------------------------------------------------------
VIRUS_ACCESSIONS = [
    "NC_045512",  # SARS-CoV-2 (Coronaviridae)
    "NC_001802",  # HIV-1 (Retroviridae)
    "NC_002549",  # Zaire ebolavirus (Filoviridae)
    "NC_001477",  # Dengue virus 1 (Flaviviridae)
    "NC_012532",  # Zika virus (Flaviviridae)
    "NC_001542",  # Rabies lyssavirus (Rhabdoviridae)
    "NC_004102",  # Hepatitis C virus genotype 1 (Flaviviridae)
    "NC_003977",  # Hepatitis B virus (Hepadnaviridae)
    "NC_001526",  # Human papillomavirus type 16 (Papillomaviridae)
    "NC_002058",  # Poliovirus 1 Mahoney (Picornaviridae)
    "NC_001348",  # Varicella-zoster virus (Herpesviridae lineage)
    "NC_006273",  # Human cytomegalovirus (Herpesviridae lineage)
    "AF086833",   # Ebola virus Mayinga, classic GenBank record
    # Influenza A virus A/Puerto Rico/8/1934 (H1N1), all eight segments
    "NC_002016", "NC_002017", "NC_002018", "NC_002019",
    "NC_002020", "NC_002021", "NC_002022", "NC_002023",
]

# ---------------------------------------------------------------------------
# Genome assemblies — NCBI Datasets (reference assemblies)
# ---------------------------------------------------------------------------
GENOME_ACCESSIONS = [
    "GCF_000001405.40",  # Homo sapiens GRCh38.p14
    "GCF_000001635.27",  # Mus musculus GRCm39
    "GCF_000005845.2",   # Escherichia coli K-12 MG1655
    "GCF_000146045.2",   # Saccharomyces cerevisiae R64
    "GCF_000001215.4",   # Drosophila melanogaster BDGP6
    "GCF_000002985.6",   # Caenorhabditis elegans WBcel235
    "GCF_000001735.4",   # Arabidopsis thaliana TAIR10
    "GCF_000195955.2",   # Mycobacterium tuberculosis H37Rv
    "GCF_009858895.2",   # SARS-CoV-2 reference assembly
    "GCF_000002035.6",   # Danio rerio GRCz11
]

_PUBMED_BACKFILL_CAP = 400


def _merge(target: ImportReport, part: ImportReport) -> None:
    target.total += part.total
    target.created += part.created
    target.updated += part.updated
    target.skipped += part.skipped
    target.failed += part.failed
    target.errors.extend(part.errors)


def _show(label: str, report: ImportReport) -> None:
    print(
        f"  {label:<34} total={report.total:<4} created={report.created:<4} "
        f"updated={report.updated:<4} skipped={report.skipped:<4} failed={report.failed}"
    )
    for error in report.errors[:5]:
        print(f"      ! {error}")
    if len(report.errors) > 5:
        print(f"      ! … and {len(report.errors) - 5} more")


async def seed_sequences(run_searches: bool) -> None:
    print("\n[1/6] DNA — curated genomic records (NCBI)")
    _show("dna curated", await ncbi.ingest(DNA_ACCESSIONS, db="nuccore"))
    if run_searches:
        for term, limit in DNA_SEARCHES:
            _show(f"dna search ({term[:24]}…)", await ncbi.ingest(term=term, limit=limit))

    print("\n[2/6] RNA — curated mRNA/ncRNA records (NCBI)")
    _show("rna curated", await ncbi.ingest(RNA_ACCESSIONS, db="nuccore"))
    if run_searches:
        for term, limit in RNA_SEARCHES:
            _show(f"rna search ({term[:24]}…)", await ncbi.ingest(term=term, limit=limit))

    print("\n[3/6] Proteins — curated UniProtKB entries")
    _show("uniprot curated", await uniprot.ingest(PROTEIN_ACCESSIONS, batch_size=1))

    print("\n[4/6] CRISPR — real CRISPR loci (NCBI)")
    if run_searches:
        for term, limit in CRISPR_SEARCHES:
            _show(
                f"crispr search ({term[:22]}…)",
                await ncbi.ingest(term=term, limit=limit, seq_type="crispr"),
            )
    else:
        print("  (skipped — term searches disabled)")

    print("\n[5/6] Viruses — complete genomes (NCBI RefSeq/GenBank)")
    _show("virus curated", await ncbi.ingest(VIRUS_ACCESSIONS, seq_type="virus", batch_size=1))

    print("\n[6/6] Genome assemblies — NCBI Datasets")
    _show("assemblies", await datasets.ingest(GENOME_ACCESSIONS))


async def backfill_publications(max_rounds: int = 10) -> None:
    """Enrich publications created from partial REFERENCE blocks via PubMed."""
    previous: set[int] = set()
    for round_number in range(1, max_rounds + 1):
        async with get_sessionmaker()() as session:
            pmids = (
                (
                    await session.execute(
                        select(Publication.pubmed_id)
                        .where(
                            Publication.pubmed_id.is_not(None),
                            (Publication.journal.is_(None))
                            | (Publication.abstract.is_(None)),
                        )
                        .order_by(Publication.pubmed_id)
                        .limit(_PUBMED_BACKFILL_CAP)
                    )
                )
                .scalars()
                .all()
            )
        if not pmids:
            print("\n[PubMed] all publications carry full metadata")
            return
        current = set(pmids)
        if current == previous:
            # Only records PubMed itself cannot complete remain (e.g. articles
            # without an abstract at the source). Nothing more to do.
            print("\n[PubMed] remaining records have no further metadata at the source")
            return
        previous = current
        print(f"\n[PubMed] round {round_number}: backfilling {len(pmids)} publication(s)")
        _show("pubmed backfill", await pubmed.ingest_pmids(list(pmids)))


async def refresh_organism_counts() -> None:
    """Recompute cached aggregates (organisms + categories) from real rows."""
    from app.services.sync_service import refresh_counts

    async with get_sessionmaker()() as session:
        result = await refresh_counts(session)
    print(f"\n[Counts] refreshed category aggregates: {result}")


async def report_totals() -> None:
    async with get_sessionmaker()() as session:
        by_type = Counter(
            dict(
                (
                    await session.execute(
                        select(Sequence.seq_type, func.count(Sequence.id)).group_by(
                            Sequence.seq_type
                        )
                    )
                ).all()
            )
        )
        organisms = (
            await session.execute(select(func.count(Organism.id)))
        ).scalar_one()
        publications = (
            await session.execute(select(func.count(Publication.id)))
        ).scalar_one()
        links = (
            await session.execute(select(func.count(SequenceReference.sequence_id)))
        ).scalar_one()
        from app.models.genome import GenomeRecord

        genomes = (
            await session.execute(select(func.count(GenomeRecord.id)))
        ).scalar_one()

    print("\n" + "=" * 60)
    print("DATABASE TOTALS (real records)")
    print("=" * 60)
    for seq_type, count in sorted(by_type.items(), key=lambda kv: str(kv[0])):
        label = seq_type.value if hasattr(seq_type, "value") else str(seq_type)
        print(f"  sequences/{label:<10} {count}")
    print(f"  genome assemblies    {genomes}")
    print(f"  organisms            {organisms}")
    print(f"  publications         {publications}")
    print(f"  sequence-publication links {links}")


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--no-search",
        action="store_true",
        help="Only ingest curated accessions (skip Entrez term searches).",
    )
    parser.add_argument(
        "--backfill-only",
        action="store_true",
        help="Skip ingestion; only backfill PubMed metadata and refresh counts.",
    )
    parser.add_argument(
        "--skip-backfill",
        action="store_true",
        help="Ingest sequences and refresh counts without the PubMed backfill pass.",
    )
    args = parser.parse_args()

    if not args.backfill_only:
        await seed_sequences(run_searches=not args.no_search)
    if not args.skip_backfill:
        await backfill_publications()
    await refresh_organism_counts()
    await report_totals()


if __name__ == "__main__":
    asyncio.run(main())
