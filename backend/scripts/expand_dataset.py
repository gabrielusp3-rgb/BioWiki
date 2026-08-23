"""Expand BIOWIKI with real NCBI / UniProt / PDB / Rfam / PubMed records.

Reuses the existing pipeline fetchers. Idempotent (upserts by official IDs).
Resumable via a JSON checkpoint. Invents nothing: every record is downloaded
from a public scientific source and validated before insert.

Run from ``backend/``:

    python -m scripts.expand_dataset
    python -m scripts.expand_dataset --pubmed-only
    python -m scripts.expand_dataset --sequences-only
"""

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Awaitable, Callable

from app.core.stdio import configure_utf8_stdio

configure_utf8_stdio()

from sqlalchemy import func, select

from app.database.session import get_sessionmaker
from app.models.genome import GenomeRecord
from app.models.organism import Organism
from app.models.publication import Publication, SequenceReference
from app.models.sequence import Sequence
from app.models.source import DataSource
from app.pipeline.fetchers import datasets, ncbi, pdb, pubmed, rfam, uniprot
from app.pipeline.models import ImportReport

SEQUENCE_TARGET = 1500
PUBLICATION_TARGET = 3500
CHECKPOINT_PATH = Path(__file__).resolve().parent.parent / "data" / "expansion_checkpoint.json"

_DNA_SLEN = "800:25000[SLEN]"
_RNA_SLEN = "400:12000[SLEN]"
_VIRUS_SLEN = "800:250000[SLEN]"
_CRISPR_SLEN = "200:40000[SLEN]"


def _dna_cds(organism: str) -> str:
    return (
        f'{organism}[Organism] AND biomol_genomic[PROP] AND '
        f'"complete cds"[Title] AND {_DNA_SLEN}'
    )


def _rna_mrna(organism: str) -> str:
    return (
        f'{organism}[Organism] AND biomol_mrna[PROP] AND refseq[filter] AND {_RNA_SLEN}'
    )


def _uniprot_reviewed(tax_id: int) -> str:
    return f"(organism_id:{tax_id}) AND (reviewed:true)"


def _virus_complete(taxon: str) -> str:
    return (
        f'{taxon}[Organism] AND "complete genome"[Title] AND '
        f"srcdb_refseq[PROP] AND {_VIRUS_SLEN}"
    )


# First pass: diversity across clades and molecule types (modest limits).
SEQUENCE_JOBS: list[dict[str, Any]] = [
    # --- DNA / mammals ---
    {"id": "dna-human", "kind": "ncbi", "term": _dna_cds("Homo sapiens"), "limit": 12, "seq_type": "dna"},
    {"id": "dna-mouse", "kind": "ncbi", "term": _dna_cds("Mus musculus"), "limit": 10, "seq_type": "dna"},
    {"id": "dna-rat", "kind": "ncbi", "term": _dna_cds("Rattus norvegicus"), "limit": 8, "seq_type": "dna"},
    {"id": "dna-cow", "kind": "ncbi", "term": _dna_cds("Bos taurus"), "limit": 6, "seq_type": "dna"},
    {"id": "dna-pig", "kind": "ncbi", "term": _dna_cds("Sus scrofa"), "limit": 6, "seq_type": "dna"},
    {"id": "dna-dog", "kind": "ncbi", "term": _dna_cds("Canis lupus familiaris"), "limit": 6, "seq_type": "dna"},
    {"id": "dna-chimp", "kind": "ncbi", "term": _dna_cds("Pan troglodytes"), "limit": 5, "seq_type": "dna"},
    # --- DNA / fish, birds, reptiles, amphibians ---
    {"id": "dna-zebrafish", "kind": "ncbi", "term": _dna_cds("Danio rerio"), "limit": 8, "seq_type": "dna"},
    {"id": "dna-medaka", "kind": "ncbi", "term": _dna_cds("Oryzias latipes"), "limit": 5, "seq_type": "dna"},
    {"id": "dna-salmon", "kind": "ncbi", "term": _dna_cds("Salmo salar"), "limit": 5, "seq_type": "dna"},
    {"id": "dna-chicken", "kind": "ncbi", "term": _dna_cds("Gallus gallus"), "limit": 8, "seq_type": "dna"},
    {"id": "dna-zebrafinch", "kind": "ncbi", "term": _dna_cds("Taeniopygia guttata"), "limit": 5, "seq_type": "dna"},
    {"id": "dna-duck", "kind": "ncbi", "term": _dna_cds("Anas platyrhynchos"), "limit": 4, "seq_type": "dna"},
    {"id": "dna-anole", "kind": "ncbi", "term": _dna_cds("Anolis carolinensis"), "limit": 5, "seq_type": "dna"},
    {"id": "dna-turtle", "kind": "ncbi", "term": _dna_cds("Chrysemys picta"), "limit": 4, "seq_type": "dna"},
    {"id": "dna-python", "kind": "ncbi", "term": _dna_cds("Python bivittatus"), "limit": 4, "seq_type": "dna"},
    {"id": "dna-xenopus", "kind": "ncbi", "term": _dna_cds("Xenopus tropicalis"), "limit": 6, "seq_type": "dna"},
    {"id": "dna-axolotl", "kind": "ncbi", "term": _dna_cds("Ambystoma mexicanum"), "limit": 4, "seq_type": "dna"},
    # --- DNA / insects, plants, fungi ---
    {"id": "dna-drosophila", "kind": "ncbi", "term": _dna_cds("Drosophila melanogaster"), "limit": 8, "seq_type": "dna"},
    {"id": "dna-mosquito", "kind": "ncbi", "term": _dna_cds("Anopheles gambiae"), "limit": 5, "seq_type": "dna"},
    {"id": "dna-honeybee", "kind": "ncbi", "term": _dna_cds("Apis mellifera"), "limit": 5, "seq_type": "dna"},
    {"id": "dna-silkworm", "kind": "ncbi", "term": _dna_cds("Bombyx mori"), "limit": 4, "seq_type": "dna"},
    {"id": "dna-arabidopsis", "kind": "ncbi", "term": _dna_cds("Arabidopsis thaliana"), "limit": 8, "seq_type": "dna"},
    {"id": "dna-rice", "kind": "ncbi", "term": _dna_cds("Oryza sativa"), "limit": 6, "seq_type": "dna"},
    {"id": "dna-maize", "kind": "ncbi", "term": _dna_cds("Zea mays"), "limit": 5, "seq_type": "dna"},
    {"id": "dna-tomato", "kind": "ncbi", "term": _dna_cds("Solanum lycopersicum"), "limit": 4, "seq_type": "dna"},
    {"id": "dna-yeast", "kind": "ncbi", "term": _dna_cds("Saccharomyces cerevisiae"), "limit": 8, "seq_type": "dna"},
    {"id": "dna-candida", "kind": "ncbi", "term": _dna_cds("Candida albicans"), "limit": 5, "seq_type": "dna"},
    {"id": "dna-aspergillus", "kind": "ncbi", "term": _dna_cds("Aspergillus nidulans"), "limit": 4, "seq_type": "dna"},
    # --- DNA / bacteria, archaea, protozoa ---
    {"id": "dna-ecoli", "kind": "ncbi", "term": _dna_cds("Escherichia coli"), "limit": 10, "seq_type": "dna"},
    {"id": "dna-bacillus", "kind": "ncbi", "term": _dna_cds("Bacillus subtilis"), "limit": 6, "seq_type": "dna"},
    {"id": "dna-staph", "kind": "ncbi", "term": _dna_cds("Staphylococcus aureus"), "limit": 6, "seq_type": "dna"},
    {"id": "dna-strep", "kind": "ncbi", "term": _dna_cds("Streptococcus pyogenes"), "limit": 5, "seq_type": "dna"},
    {"id": "dna-salmonella", "kind": "ncbi", "term": _dna_cds("Salmonella enterica"), "limit": 5, "seq_type": "dna"},
    {"id": "dna-pseudo", "kind": "ncbi", "term": _dna_cds("Pseudomonas aeruginosa"), "limit": 5, "seq_type": "dna"},
    {"id": "dna-mtb", "kind": "ncbi", "term": _dna_cds("Mycobacterium tuberculosis"), "limit": 5, "seq_type": "dna"},
    {"id": "dna-vibrio", "kind": "ncbi", "term": _dna_cds("Vibrio cholerae"), "limit": 4, "seq_type": "dna"},
    {"id": "dna-helicobacter", "kind": "ncbi", "term": _dna_cds("Helicobacter pylori"), "limit": 4, "seq_type": "dna"},
    {"id": "dna-listeria", "kind": "ncbi", "term": _dna_cds("Listeria monocytogenes"), "limit": 4, "seq_type": "dna"},
    {"id": "dna-methano", "kind": "ncbi", "term": _dna_cds("Methanocaldococcus jannaschii"), "limit": 5, "seq_type": "dna"},
    {"id": "dna-haloferax", "kind": "ncbi", "term": _dna_cds("Haloferax volcanii"), "limit": 4, "seq_type": "dna"},
    {"id": "dna-sulfolobus", "kind": "ncbi", "term": _dna_cds("Saccharolobus solfataricus"), "limit": 4, "seq_type": "dna"},
    {"id": "dna-plasmodium", "kind": "ncbi", "term": _dna_cds("Plasmodium falciparum"), "limit": 5, "seq_type": "dna"},
    {"id": "dna-trypanosoma", "kind": "ncbi", "term": _dna_cds("Trypanosoma brucei"), "limit": 4, "seq_type": "dna"},
    # --- RNA ---
    {"id": "rna-human", "kind": "ncbi", "term": _rna_mrna("Homo sapiens"), "limit": 12, "seq_type": "rna"},
    {"id": "rna-mouse", "kind": "ncbi", "term": _rna_mrna("Mus musculus"), "limit": 8, "seq_type": "rna"},
    {"id": "rna-rat", "kind": "ncbi", "term": _rna_mrna("Rattus norvegicus"), "limit": 6, "seq_type": "rna"},
    {"id": "rna-zebrafish", "kind": "ncbi", "term": _rna_mrna("Danio rerio"), "limit": 8, "seq_type": "rna"},
    {"id": "rna-chicken", "kind": "ncbi", "term": _rna_mrna("Gallus gallus"), "limit": 6, "seq_type": "rna"},
    {"id": "rna-xenopus", "kind": "ncbi", "term": _rna_mrna("Xenopus tropicalis"), "limit": 5, "seq_type": "rna"},
    {"id": "rna-drosophila", "kind": "ncbi", "term": _rna_mrna("Drosophila melanogaster"), "limit": 8, "seq_type": "rna"},
    {"id": "rna-celegans", "kind": "ncbi", "term": _rna_mrna("Caenorhabditis elegans"), "limit": 6, "seq_type": "rna"},
    {"id": "rna-arabidopsis", "kind": "ncbi", "term": _rna_mrna("Arabidopsis thaliana"), "limit": 8, "seq_type": "rna"},
    {"id": "rna-rice", "kind": "ncbi", "term": _rna_mrna("Oryza sativa"), "limit": 5, "seq_type": "rna"},
    {"id": "rna-yeast", "kind": "ncbi", "term": _rna_mrna("Saccharomyces cerevisiae"), "limit": 6, "seq_type": "rna"},
    {"id": "rna-16s", "kind": "ncbi",
     "term": f'"16S ribosomal RNA"[Title] AND refseq[filter] AND 1200:1800[SLEN]',
     "limit": 20, "seq_type": "rna"},
    {"id": "rna-lncrna", "kind": "ncbi",
     "term": 'Homo sapiens[Organism] AND biomol_ncrna[PROP] AND refseq[filter] AND 200:20000[SLEN]',
     "limit": 10, "seq_type": "rna"},
    {"id": "rfam-5s", "kind": "rfam", "family": "RF00001", "limit": 8},
    {"id": "rfam-trna", "kind": "rfam", "family": "RF00005", "limit": 8},
    {"id": "rfam-u2", "kind": "rfam", "family": "RF00004", "limit": 6},
    {"id": "rfam-ssu", "kind": "rfam", "family": "RF00177", "limit": 6},
    # --- Proteins (UniProt Swiss-Prot) ---
    {"id": "prot-human", "kind": "uniprot", "query": _uniprot_reviewed(9606), "limit": 18},
    {"id": "prot-mouse", "kind": "uniprot", "query": _uniprot_reviewed(10090), "limit": 10},
    {"id": "prot-rat", "kind": "uniprot", "query": _uniprot_reviewed(10116), "limit": 6},
    {"id": "prot-zebrafish", "kind": "uniprot", "query": _uniprot_reviewed(7955), "limit": 6},
    {"id": "prot-chicken", "kind": "uniprot", "query": _uniprot_reviewed(9031), "limit": 5},
    {"id": "prot-xenopus", "kind": "uniprot", "query": _uniprot_reviewed(8364), "limit": 4},
    {"id": "prot-drosophila", "kind": "uniprot", "query": _uniprot_reviewed(7227), "limit": 8},
    {"id": "prot-celegans", "kind": "uniprot", "query": _uniprot_reviewed(6239), "limit": 5},
    {"id": "prot-arabidopsis", "kind": "uniprot", "query": _uniprot_reviewed(3702), "limit": 8},
    {"id": "prot-rice", "kind": "uniprot", "query": _uniprot_reviewed(39947), "limit": 4},
    {"id": "prot-yeast", "kind": "uniprot", "query": _uniprot_reviewed(559292), "limit": 8},
    {"id": "prot-ecoli", "kind": "uniprot", "query": _uniprot_reviewed(83333), "limit": 8},
    {"id": "prot-staph", "kind": "uniprot", "query": _uniprot_reviewed(1280), "limit": 4},
    {"id": "prot-mtb", "kind": "uniprot", "query": _uniprot_reviewed(1773), "limit": 4},
    {"id": "prot-pyogenes", "kind": "uniprot", "query": _uniprot_reviewed(1314), "limit": 4},
    {"id": "prot-halobacterium", "kind": "uniprot", "query": _uniprot_reviewed(2242), "limit": 4},
    {"id": "prot-plasmodium", "kind": "uniprot", "query": _uniprot_reviewed(5833), "limit": 4},
    {"id": "prot-sars2", "kind": "uniprot", "query": _uniprot_reviewed(2697049), "limit": 8},
    # --- PDB structures (real PDB IDs) ---
    {"id": "pdb-core", "kind": "pdb", "ids": [
        "4HHB", "1BNA", "1EHZ", "1MBO", "1INS", "2LYZ", "1UBQ", "1CRN",
        "3CLN", "1GFL", "1AKE", "2HHB", "1HHO", "3NIR", "1L2Y",
    ]},
    # --- CRISPR loci ---
    {"id": "crispr-general", "kind": "ncbi",
     "term": f'CRISPR[Title] AND (array[Title] OR "repeat region"[Title] OR locus[Title]) AND {_CRISPR_SLEN}',
     "limit": 30, "seq_type": "crispr"},
    {"id": "crispr-strep", "kind": "ncbi",
     "term": f'CRISPR[Title] AND Streptococcus[Organism] AND {_CRISPR_SLEN}',
     "limit": 15, "seq_type": "crispr"},
    {"id": "crispr-ecoli", "kind": "ncbi",
     "term": f'CRISPR[Title] AND Escherichia[Organism] AND {_CRISPR_SLEN}',
     "limit": 10, "seq_type": "crispr"},
    {"id": "crispr-pyogenes", "kind": "ncbi",
     "term": f'CRISPR[Title] AND "Streptococcus pyogenes"[Organism] AND {_CRISPR_SLEN}',
     "limit": 8, "seq_type": "crispr"},
    {"id": "crispr-cas12", "kind": "ncbi",
     "term": f'(Cas12 OR Cpf1 OR Cas13)[Title] AND CRISPR AND {_CRISPR_SLEN}',
     "limit": 10, "seq_type": "crispr"},
    # --- Viruses ---
    {"id": "virus-corona", "kind": "ncbi", "term": _virus_complete("Coronaviridae"), "limit": 8, "seq_type": "virus"},
    {"id": "virus-ortho", "kind": "ncbi", "term": _virus_complete("Orthomyxoviridae"), "limit": 10, "seq_type": "virus"},
    {"id": "virus-flavi", "kind": "ncbi", "term": _virus_complete("Flaviviridae"), "limit": 8, "seq_type": "virus"},
    {"id": "virus-herpes", "kind": "ncbi", "term": _virus_complete("Herpesviridae"), "limit": 6, "seq_type": "virus"},
    {"id": "virus-papilloma", "kind": "ncbi", "term": _virus_complete("Papillomaviridae"), "limit": 6, "seq_type": "virus"},
    {"id": "virus-retro", "kind": "ncbi", "term": _virus_complete("Retroviridae"), "limit": 6, "seq_type": "virus"},
    {"id": "virus-rhabdo", "kind": "ncbi", "term": _virus_complete("Rhabdoviridae"), "limit": 5, "seq_type": "virus"},
    {"id": "virus-filo", "kind": "ncbi", "term": _virus_complete("Filoviridae"), "limit": 4, "seq_type": "virus"},
    {"id": "virus-adeno", "kind": "ncbi", "term": _virus_complete("Adenoviridae"), "limit": 5, "seq_type": "virus"},
    {"id": "virus-pox", "kind": "ncbi", "term": _virus_complete("Poxviridae"), "limit": 4, "seq_type": "virus"},
    {"id": "virus-picorna", "kind": "ncbi", "term": _virus_complete("Picornaviridae"), "limit": 6, "seq_type": "virus"},
    {"id": "virus-phage", "kind": "ncbi", "term": _virus_complete("Caudoviricetes"), "limit": 6, "seq_type": "virus"},
    # --- Genome assemblies (NCBI Datasets; not sequence residues) ---
    {"id": "asm-human", "kind": "genomes", "taxon": "Homo sapiens", "limit": 2},
    {"id": "asm-mouse", "kind": "genomes", "taxon": "Mus musculus", "limit": 2},
    {"id": "asm-zebrafish", "kind": "genomes", "taxon": "Danio rerio", "limit": 2},
    {"id": "asm-chicken", "kind": "genomes", "taxon": "Gallus gallus", "limit": 2},
    {"id": "asm-anole", "kind": "genomes", "taxon": "Anolis carolinensis", "limit": 1},
    {"id": "asm-xenopus", "kind": "genomes", "taxon": "Xenopus tropicalis", "limit": 1},
    {"id": "asm-drosophila", "kind": "genomes", "taxon": "Drosophila melanogaster", "limit": 1},
    {"id": "asm-arabidopsis", "kind": "genomes", "taxon": "Arabidopsis thaliana", "limit": 1},
    {"id": "asm-rice", "kind": "genomes", "taxon": "Oryza sativa", "limit": 1},
    {"id": "asm-yeast", "kind": "genomes", "taxon": "Saccharomyces cerevisiae", "limit": 1},
    {"id": "asm-ecoli", "kind": "genomes", "taxon": "Escherichia coli", "limit": 3},
    {"id": "asm-staph", "kind": "genomes", "taxon": "Staphylococcus aureus", "limit": 2},
    {"id": "asm-mtb", "kind": "genomes", "taxon": "Mycobacterium tuberculosis", "limit": 2},
    {"id": "asm-bacillus", "kind": "genomes", "taxon": "Bacillus subtilis", "limit": 1},
    {"id": "asm-pseudo", "kind": "genomes", "taxon": "Pseudomonas aeruginosa", "limit": 1},
    {"id": "asm-methano", "kind": "genomes", "taxon": "Methanocaldococcus jannaschii", "limit": 1},
    {"id": "asm-haloferax", "kind": "genomes", "taxon": "Haloferax volcanii", "limit": 1},
    {"id": "asm-plasmodium", "kind": "genomes", "taxon": "Plasmodium falciparum", "limit": 1},
]

FILL_JOBS: list[dict[str, Any]] = [
    {"id": "fill-dna-human2", "kind": "ncbi",
     "term": 'Homo sapiens[Organism] AND biomol_genomic[PROP] AND gene[Title] AND 1000:20000[SLEN] AND refseq[filter]',
     "limit": 25, "seq_type": "dna"},
    {"id": "fill-dna-bacteria", "kind": "ncbi",
     "term": 'Bacteria[Organism] AND biomol_genomic[PROP] AND "complete cds"[Title] AND 1000:8000[SLEN]',
     "limit": 30, "seq_type": "dna"},
    {"id": "fill-dna-archaea", "kind": "ncbi",
     "term": 'Archaea[Organism] AND biomol_genomic[PROP] AND "complete cds"[Title] AND 800:12000[SLEN]',
     "limit": 15, "seq_type": "dna"},
    {"id": "fill-rna-plants", "kind": "ncbi",
     "term": 'Viridiplantae[Organism] AND biomol_mrna[PROP] AND refseq[filter] AND 500:8000[SLEN]',
     "limit": 20, "seq_type": "rna"},
    {"id": "fill-rna-fungi", "kind": "ncbi",
     "term": 'Fungi[Organism] AND biomol_mrna[PROP] AND refseq[filter] AND 400:8000[SLEN]',
     "limit": 15, "seq_type": "rna"},
    {"id": "fill-rna-trna", "kind": "ncbi",
     "term": '"tRNA"[Title] AND refseq[filter] AND 70:100[SLEN]',
     "limit": 15, "seq_type": "rna"},
    {"id": "fill-prot-bacteria", "kind": "uniprot",
     "query": "(taxonomy_id:2) AND (reviewed:true) AND (length:[100 TO 800])", "limit": 25},
    {"id": "fill-prot-plants", "kind": "uniprot",
     "query": "(taxonomy_id:33090) AND (reviewed:true) AND (length:[80 TO 800])", "limit": 15},
    {"id": "fill-prot-fungi", "kind": "uniprot",
     "query": "(taxonomy_id:4751) AND (reviewed:true) AND (length:[80 TO 800])", "limit": 12},
    {"id": "fill-prot-archaea", "kind": "uniprot",
     "query": "(taxonomy_id:2157) AND (reviewed:true) AND (length:[80 TO 800])", "limit": 10},
    {"id": "fill-virus-more", "kind": "ncbi",
     "term": 'Viruses[Organism] AND "complete genome"[Title] AND srcdb_refseq[PROP] AND 2000:40000[SLEN]',
     "limit": 25, "seq_type": "virus"},
    {"id": "fill-crispr-more", "kind": "ncbi",
     "term": f'CRISPR[All Fields] AND cas[Title] AND {_CRISPR_SLEN}',
     "limit": 20, "seq_type": "crispr"},
]

# Third pass: additional real records when the first two passes stay under target.
EXTRA_JOBS: list[dict[str, Any]] = [
    {"id": "x-dna-mammalia", "kind": "ncbi",
     "term": f'Mammalia[Organism] AND biomol_genomic[PROP] AND "complete cds"[Title] AND {_DNA_SLEN}',
     "limit": 50, "seq_type": "dna"},
    {"id": "x-dna-aves", "kind": "ncbi",
     "term": f'Aves[Organism] AND biomol_genomic[PROP] AND "complete cds"[Title] AND {_DNA_SLEN}',
     "limit": 30, "seq_type": "dna"},
    {"id": "x-dna-reptilia", "kind": "ncbi",
     "term": f'Reptilia[Organism] AND biomol_genomic[PROP] AND "complete cds"[Title] AND {_DNA_SLEN}',
     "limit": 20, "seq_type": "dna"},
    {"id": "x-dna-amphibia", "kind": "ncbi",
     "term": f'Amphibia[Organism] AND biomol_genomic[PROP] AND "complete cds"[Title] AND {_DNA_SLEN}',
     "limit": 20, "seq_type": "dna"},
    {"id": "x-dna-fish", "kind": "ncbi",
     "term": f'Actinopterygii[Organism] AND biomol_genomic[PROP] AND "complete cds"[Title] AND {_DNA_SLEN}',
     "limit": 30, "seq_type": "dna"},
    {"id": "x-dna-insecta", "kind": "ncbi",
     "term": f'Insecta[Organism] AND biomol_genomic[PROP] AND "complete cds"[Title] AND {_DNA_SLEN}',
     "limit": 30, "seq_type": "dna"},
    {"id": "x-dna-plants", "kind": "ncbi",
     "term": f'Viridiplantae[Organism] AND biomol_genomic[PROP] AND "complete cds"[Title] AND {_DNA_SLEN}',
     "limit": 30, "seq_type": "dna"},
    {"id": "x-dna-fungi", "kind": "ncbi",
     "term": f'Fungi[Organism] AND biomol_genomic[PROP] AND "complete cds"[Title] AND {_DNA_SLEN}',
     "limit": 25, "seq_type": "dna"},
    {"id": "x-dna-bacteria2", "kind": "ncbi",
     "term": f'Bacteria[Organism] AND biomol_genomic[PROP] AND "complete cds"[Title] AND 2000:6000[SLEN]',
     "limit": 50, "seq_type": "dna"},
    {"id": "x-dna-archaea2", "kind": "ncbi",
     "term": f'Archaea[Organism] AND biomol_genomic[PROP] AND "complete cds"[Title] AND 1500:8000[SLEN]',
     "limit": 20, "seq_type": "dna"},
    {"id": "x-rna-mammalia", "kind": "ncbi",
     "term": f'Mammalia[Organism] AND biomol_mrna[PROP] AND refseq[filter] AND {_RNA_SLEN}',
     "limit": 40, "seq_type": "rna"},
    {"id": "x-rna-aves", "kind": "ncbi",
     "term": f'Aves[Organism] AND biomol_mrna[PROP] AND refseq[filter] AND {_RNA_SLEN}',
     "limit": 20, "seq_type": "rna"},
    {"id": "x-rna-fish", "kind": "ncbi",
     "term": f'Actinopterygii[Organism] AND biomol_mrna[PROP] AND refseq[filter] AND {_RNA_SLEN}',
     "limit": 20, "seq_type": "rna"},
    {"id": "x-rna-insecta", "kind": "ncbi",
     "term": f'Insecta[Organism] AND biomol_mrna[PROP] AND refseq[filter] AND {_RNA_SLEN}',
     "limit": 20, "seq_type": "rna"},
    {"id": "x-rna-ncrna", "kind": "ncbi",
     "term": 'biomol_ncrna[PROP] AND refseq[filter] AND 100:8000[SLEN]',
     "limit": 25, "seq_type": "rna"},
    {"id": "x-prot-kinase", "kind": "uniprot",
     "query": "(reviewed:true) AND (keyword:KW-0418) AND (length:[200 TO 500])", "limit": 20},
    {"id": "x-prot-ribosomal", "kind": "uniprot",
     "query": "(reviewed:true) AND (keyword:KW-0689) AND (length:[50 TO 250])", "limit": 20},
    {"id": "x-prot-hemoglobin", "kind": "uniprot",
     "query": "(reviewed:true) AND (name:hemoglobin) AND (length:[100 TO 200])", "limit": 15},
    {"id": "x-prot-virus2", "kind": "uniprot",
     "query": "(taxonomy_id:10239) AND (reviewed:true) AND (length:[100 TO 600])", "limit": 20},
    {"id": "x-prot-archaea2", "kind": "uniprot",
     "query": "(taxonomy_id:2157) AND (reviewed:true) AND (length:[250 TO 500])", "limit": 12},
    {"id": "x-prot-insect", "kind": "uniprot",
     "query": "(taxonomy_id:50557) AND (reviewed:true) AND (length:[80 TO 400])", "limit": 12},
    {"id": "x-prot-bird", "kind": "uniprot",
     "query": "(taxonomy_id:8782) AND (reviewed:true) AND (length:[80 TO 400])", "limit": 10},
    {"id": "x-prot-fish", "kind": "uniprot",
     "query": "(taxonomy_id:7898) AND (reviewed:true) AND (length:[80 TO 400])", "limit": 10},
    {"id": "x-crispr-bacteria", "kind": "ncbi",
     "term": f'CRISPR[Title] AND Bacteria[Organism] AND {_CRISPR_SLEN}',
     "limit": 30, "seq_type": "crispr"},
    {"id": "x-virus-refseq2", "kind": "ncbi",
     "term": 'Viruses[Organism] AND "complete genome"[Title] AND srcdb_refseq[PROP] AND 800:15000[SLEN]',
     "limit": 40, "seq_type": "virus"},
    {"id": "x-pdb-core", "kind": "pdb", "ids": [
        "4HHB", "1MBO", "1INS", "2LYZ", "1UBQ", "1CRN", "3CLN", "1GFL",
        "1AKE", "1TIM", "1MBN", "5P21", "1PGA", "4INS", "1LYZ", "3TGI",
        "1HHO", "2HHB", "1GZX", "1AKG",
    ]},
]

EXTRA2_JOBS: list[dict[str, Any]] = [
    {"id": "y-dna-mammal-mid", "kind": "ncbi",
     "term": 'Mammalia[Organism] AND biomol_genomic[PROP] AND "complete cds"[Title] AND 3000:9000[SLEN]',
     "limit": 40, "seq_type": "dna"},
    {"id": "y-dna-bacteria-mid", "kind": "ncbi",
     "term": 'Bacteria[Organism] AND biomol_genomic[PROP] AND "complete cds"[Title] AND 4000:9000[SLEN]',
     "limit": 40, "seq_type": "dna"},
    {"id": "y-dna-plants-mid", "kind": "ncbi",
     "term": 'Viridiplantae[Organism] AND biomol_genomic[PROP] AND "complete cds"[Title] AND 2500:8000[SLEN]',
     "limit": 20, "seq_type": "dna"},
    {"id": "y-rna-amphibia", "kind": "ncbi",
     "term": 'Amphibia[Organism] AND biomol_mrna[PROP] AND refseq[filter] AND 500:8000[SLEN]',
     "limit": 15, "seq_type": "rna"},
    {"id": "y-rna-reptilia", "kind": "ncbi",
     "term": 'Reptilia[Organism] AND biomol_mrna[PROP] AND refseq[filter] AND 500:8000[SLEN]',
     "limit": 12, "seq_type": "rna"},
    {"id": "y-prot-membrane", "kind": "uniprot",
     "query": "(reviewed:true) AND (keyword:KW-0472) AND (length:[150 TO 350])", "limit": 20},
    {"id": "y-prot-dna-bind", "kind": "uniprot",
     "query": "(reviewed:true) AND (keyword:KW-0238) AND (length:[80 TO 250])", "limit": 15},
    {"id": "y-virus-ssrna", "kind": "ncbi",
     "term": 'Viruses[Organism] AND "complete genome"[Title] AND srcdb_refseq[PROP] AND 7000:12000[SLEN]',
     "limit": 15, "seq_type": "virus"},
    {"id": "y-crispr-bacillus", "kind": "ncbi",
     "term": f'CRISPR[Title] AND Bacillus[Organism] AND {_CRISPR_SLEN}',
     "limit": 12, "seq_type": "crispr"},
    {"id": "y-pdb-retry", "kind": "pdb", "ids": [
        "4HHB", "1MBO", "1INS", "2LYZ", "1UBQ", "1CRN", "3CLN", "1GFL",
        "1AKE", "1TIM", "1MBN", "5P21", "1PGA", "4INS", "1LYZ", "3TGI",
        "1HHO", "2HHB", "1GZX",
    ]},
]

PUBMED_SEARCHES: list[tuple[str, str, int]] = [
    ("pm-crispr", "CRISPR[Title] AND Cas9[Title] AND (genome[Title] OR gene[Title])", 200),
    ("pm-tp53", "TP53[Title] AND (mutation[Title] OR genome[Title]) AND humans[MeSH]", 150),
    ("pm-brca", "(BRCA1[Title] OR BRCA2[Title]) AND (cancer[Title] OR genome[Title])", 150),
    ("pm-insulin", "insulin[Title] AND (gene[Title] OR receptor[Title]) AND humans[MeSH]", 120),
    ("pm-egfr", "EGFR[Title] AND (mutation[Title] OR inhibitor[Title])", 120),
    ("pm-sars2", "SARS-CoV-2[Title] AND (spike[Title] OR genome[Title])", 200),
    ("pm-influenza", "influenza[Title] AND (hemagglutinin[Title] OR genome[Title])", 120),
    ("pm-hiv", "HIV-1[Title] AND (genome[Title] OR envelope[Title])", 100),
    ("pm-mtb", "Mycobacterium tuberculosis[Title] AND (genome[Title] OR CRISPR[Title])", 100),
    ("pm-ecoli", "Escherichia coli[Title] AND (genome[Title] OR CRISPR[Title])", 100),
    ("pm-arabidopsis", "Arabidopsis thaliana[Title] AND (genome[Title] OR gene[Title])", 120),
    ("pm-drosophila", "Drosophila melanogaster[Title] AND (genome[Title] OR development[Title])", 120),
    ("pm-zebrafish", "Danio rerio[Title] AND (genome[Title] OR development[Title])", 100),
    ("pm-yeast", "Saccharomyces cerevisiae[Title] AND (genome[Title] OR gene[Title])", 100),
    ("pm-plasmodium", "Plasmodium falciparum[Title] AND (genome[Title] OR vaccine[Title])", 80),
    ("pm-xenopus", "Xenopus[Title] AND (genome[Title] OR development[Title])", 60),
    ("pm-chicken", "Gallus gallus[Title] AND (genome[Title] OR gene[Title])", 60),
    ("pm-anole", "Anolis carolinensis[Title] AND genome[Title]", 40),
    ("pm-archaea", "Archaea[Title] AND (CRISPR[Title] OR genome[Title])", 80),
    ("pm-rfam", "noncoding RNA[Title] AND (Rfam[Title] OR ribosome[Title])", 80),
]


def _source_job_failed(report: ImportReport) -> bool:
    """True when a job produced no persisted records and reported a source failure."""
    return (
        report.failed > 0
        and report.created == 0
        and report.updated == 0
        and report.skipped == 0
    )


def _mark_failed(checkpoint: dict[str, Any], job_id: str, error: str) -> None:
    checkpoint.setdefault("failed", {})[job_id] = error
    _save_checkpoint(checkpoint)


def _mark_completed(checkpoint: dict[str, Any], job_id: str, report: ImportReport) -> None:
    completed = set(checkpoint.get("completed") or [])
    completed.add(job_id)
    checkpoint["completed"] = sorted(completed)
    failed = checkpoint.setdefault("failed", {})
    if job_id in failed:
        history = checkpoint.setdefault("failed_history", {})
        history[job_id] = failed.pop(job_id)
    checkpoint.setdefault("reports", []).append({"id": job_id, **report.as_dict()})
    _save_checkpoint(checkpoint)


def _merge(target: ImportReport, part: ImportReport) -> None:
    target.total += part.total
    target.created += part.created
    target.updated += part.updated
    target.skipped += part.skipped
    target.failed += part.failed
    target.errors.extend(part.errors)


def _show(label: str, report: ImportReport) -> None:
    print(
        f"  {label:<36} total={report.total:<4} created={report.created:<4} "
        f"updated={report.updated:<4} skipped={report.skipped:<4} failed={report.failed}"
    )
    for error in report.errors[:4]:
        print(f"      ! {error}")
    if len(report.errors) > 4:
        print(f"      ! … and {len(report.errors) - 4} more")


def _load_checkpoint() -> dict[str, Any]:
    if not CHECKPOINT_PATH.exists():
        return {
            "completed": [],
            "failed": {},
            "failed_history": {},
            "before": None,
            "reports": [],
            "started_at": datetime.now(timezone.utc).isoformat(),
            "notes": {},
        }
    return json.loads(CHECKPOINT_PATH.read_text(encoding="utf-8"))


def _save_checkpoint(data: dict[str, Any]) -> None:
    CHECKPOINT_PATH.parent.mkdir(parents=True, exist_ok=True)
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    CHECKPOINT_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


async def snapshot() -> dict[str, Any]:
    async with get_sessionmaker()() as session:
        by_type = {
            (seq_type.value if hasattr(seq_type, "value") else str(seq_type)): int(count)
            for seq_type, count in (
                await session.execute(
                    select(Sequence.seq_type, func.count(Sequence.id)).group_by(Sequence.seq_type)
                )
            ).all()
        }
        by_source = {
            str(key): int(count)
            for key, count in (
                await session.execute(
                    select(DataSource.key, func.count(Sequence.id))
                    .join(Sequence, Sequence.source_id == DataSource.id)
                    .group_by(DataSource.key)
                )
            ).all()
        }
        by_group = {
            (group.value if hasattr(group, "value") else str(group)): int(count)
            for group, count in (
                await session.execute(
                    select(Organism.group, func.count(Organism.id)).group_by(Organism.group)
                )
            ).all()
        }
        dup_rows = (
            await session.execute(
                select(Sequence.accession, Sequence.source_id, Sequence.version)
                .group_by(Sequence.accession, Sequence.source_id, Sequence.version)
                .having(func.count() > 1)
            )
        ).all()
        dupes = len(dup_rows)
        return {
            "sequences": int((await session.execute(select(func.count(Sequence.id)))).scalar_one()),
            "by_type": by_type,
            "by_source": by_source,
            "organisms": int((await session.execute(select(func.count(Organism.id)))).scalar_one()),
            "organism_groups": by_group,
            "publications": int(
                (await session.execute(select(func.count(Publication.id)))).scalar_one()
            ),
            "sequence_links": int(
                (await session.execute(select(func.count(SequenceReference.sequence_id)))).scalar_one()
            ),
            "genomes": int(
                (await session.execute(select(func.count(GenomeRecord.id)))).scalar_one()
            ),
            "duplicate_keys": dupes,
        }


async def _run_job(job: dict[str, Any]) -> ImportReport:
    kind = job["kind"]
    if kind == "ncbi":
        return await ncbi.ingest(
            term=job["term"],
            limit=int(job["limit"]),
            seq_type=job.get("seq_type"),
            db=job.get("db", "nuccore"),
        )
    if kind == "uniprot":
        return await uniprot.ingest(query=job["query"], limit=int(job["limit"]))
    if kind == "pdb":
        return await pdb.ingest(job["ids"])
    if kind == "rfam":
        return await rfam.ingest_family(job["family"], limit=int(job["limit"]))
    if kind == "genomes":
        return await datasets.ingest(taxon=job["taxon"], limit=int(job["limit"]))
    raise ValueError(f"unknown job kind: {kind}")


async def _retry(factory: Callable[[], Awaitable[ImportReport]], *, attempts: int = 3) -> ImportReport:
    last: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return await factory()
        except Exception as exc:  # noqa: BLE001 — transient upstream failures
            last = exc
            message = str(exc).lower()
            if "not found" in message or "404" in message:
                raise
            wait = min(2 ** attempt, 30)
            print(f"      retry {attempt}/{attempts} after error: {exc} (sleep {wait}s)")
            await asyncio.sleep(wait)
    raise last  # type: ignore[misc]


async def run_sequence_jobs(checkpoint: dict[str, Any], jobs: list[dict[str, Any]]) -> ImportReport:
    combined = ImportReport()
    completed = set(checkpoint.get("completed") or [])
    for job in jobs:
        job_id = job["id"]
        stats = await snapshot()
        if stats["sequences"] >= SEQUENCE_TARGET and not job_id.startswith("asm-"):
            print(f"  skip {job_id}: sequence target {SEQUENCE_TARGET} already reached ({stats['sequences']})")
            if job_id not in completed:
                completed.add(job_id)
                checkpoint["completed"] = sorted(completed)
                _save_checkpoint(checkpoint)
            continue
        if job_id in completed:
            print(f"  skip {job_id}: already in checkpoint")
            continue
        failed_map = checkpoint.get("failed") or {}
        if job_id in failed_map:
            print(f"  retry {job_id}: previously failed ({failed_map[job_id][:80]})")
        print(f"\n[{job_id}] {job['kind']} limit={job.get('limit', '-')}")
        try:
            report = await _retry(lambda j=job: _run_job(j))
        except Exception as exc:  # noqa: BLE001
            _mark_failed(checkpoint, job_id, str(exc))
            print(f"      FAILED {job_id}: {exc}")
            continue
        _show(job_id, report)
        if _source_job_failed(report):
            _mark_failed(checkpoint, job_id, "; ".join(report.errors[:3]) or "source unavailable")
            print(f"      FAILED {job_id}: source unavailable (not marked completed)")
            continue
        _merge(combined, report)
        checkpoint["last_stats"] = await snapshot()
        _mark_completed(checkpoint, job_id, report)
        completed = set(checkpoint.get("completed") or [])
    return combined


async def run_pubmed(checkpoint: dict[str, Any]) -> ImportReport:
    combined = ImportReport()
    completed = set(checkpoint.get("completed") or [])

    # 1) NCBI ELink from stored nucleotide accessions → real citing papers.
    elink_id = "pubmed-elink-nuccore"
    if elink_id not in completed:
        async with get_sessionmaker()() as session:
            accessions = list(
                (
                    await session.execute(
                        select(Sequence.accession)
                        .join(DataSource, Sequence.source_id == DataSource.id)
                        .where(DataSource.key.in_(["ncbi_genbank", "ncbi_refseq"]))
                        .limit(400)
                    )
                )
                .scalars()
                .all()
            )
        print(f"\n[{elink_id}] {len(accessions)} NCBI accession(s)")
        try:
            report = await _retry(lambda: pubmed.ingest_elinks(accessions, dbfrom="nuccore", max_pmids=1500))
            _show(elink_id, report)
            _merge(combined, report)
            completed.add(elink_id)
        except Exception as exc:  # noqa: BLE001
            checkpoint.setdefault("failed", {})[elink_id] = str(exc)
            print(f"      FAILED {elink_id}: {exc}")
        checkpoint["completed"] = sorted(completed)
        checkpoint["last_stats"] = await snapshot()
        _save_checkpoint(checkpoint)

    # 2) Topic searches related to organisms/genes already in BIOWIKI.
    for search_id, term, limit in PUBMED_SEARCHES:
        stats = await snapshot()
        if stats["publications"] >= PUBLICATION_TARGET:
            print(f"  skip {search_id}: publication target reached ({stats['publications']})")
            break
        if search_id in completed:
            print(f"  skip {search_id}: already in checkpoint")
            continue
        remaining = PUBLICATION_TARGET - stats["publications"]
        page_limit = min(limit, max(remaining + 50, 50), 400)
        print(f"\n[{search_id}] PubMed search limit={page_limit}")
        try:
            report = await _retry(lambda t=term, n=page_limit: pubmed.ingest_search(t, limit=n))
        except Exception as exc:  # noqa: BLE001
            checkpoint.setdefault("failed", {})[search_id] = str(exc)
            _save_checkpoint(checkpoint)
            print(f"      FAILED {search_id}: {exc}")
            continue
        _show(search_id, report)
        _merge(combined, report)
        completed.add(search_id)
        checkpoint["completed"] = sorted(completed)
        checkpoint["last_stats"] = await snapshot()
        checkpoint.setdefault("reports", []).append({"id": search_id, **report.as_dict()})
        _save_checkpoint(checkpoint)

        # Extra pages when this term still has unique hits and we are short.
        stats = await snapshot()
        if stats["publications"] < PUBLICATION_TARGET and report.created > 0:
            extra_id = f"{search_id}-p2"
            if extra_id not in completed:
                print(f"\n[{extra_id}] PubMed search retstart={page_limit}")
                try:
                    extra = await _retry(
                        lambda t=term, n=page_limit: pubmed.ingest_search(t, limit=n, retstart=n)
                    )
                    _show(extra_id, extra)
                    _merge(combined, extra)
                    completed.add(extra_id)
                    checkpoint["completed"] = sorted(completed)
                    checkpoint["last_stats"] = await snapshot()
                    _save_checkpoint(checkpoint)
                except Exception as exc:  # noqa: BLE001
                    checkpoint.setdefault("failed", {})[extra_id] = str(exc)
                    print(f"      FAILED {extra_id}: {exc}")
                    _save_checkpoint(checkpoint)

    # 3) Backfill abstracts/journals for PMIDs created from GenBank REFERENCE.
    backfill_id = "pubmed-backfill"
    if backfill_id not in completed:
        print(f"\n[{backfill_id}]")
        async with get_sessionmaker()() as session:
            pmids = list(
                (
                    await session.execute(
                        select(Publication.pubmed_id)
                        .where(
                            Publication.pubmed_id.is_not(None),
                            (Publication.journal.is_(None)) | (Publication.abstract.is_(None)),
                        )
                        .order_by(Publication.pubmed_id)
                        .limit(400)
                    )
                )
                .scalars()
                .all()
            )
        if pmids:
            try:
                report = await _retry(lambda: pubmed.ingest_pmids(list(pmids)))
                _show(backfill_id, report)
                _merge(combined, report)
            except Exception as exc:  # noqa: BLE001
                checkpoint.setdefault("failed", {})[backfill_id] = str(exc)
                print(f"      FAILED {backfill_id}: {exc}")
        completed.add(backfill_id)
        checkpoint["completed"] = sorted(completed)
        checkpoint["last_stats"] = await snapshot()
        _save_checkpoint(checkpoint)

    return combined


async def refresh_and_integrity() -> dict[str, Any]:
    from app.services import sync_service

    async with get_sessionmaker()() as session:
        refreshed = await sync_service.refresh_counts(session)
        integrity = await sync_service.check_integrity(session)
    return {
        "refreshed": refreshed,
        "integrity": integrity.model_dump(by_alias=True, mode="json"),
    }


def _print_snapshot(label: str, data: dict[str, Any]) -> None:
    print("\n" + "=" * 64)
    print(label)
    print("=" * 64)
    print(f"  sequences      {data['sequences']}")
    for key, value in sorted((data.get("by_type") or {}).items()):
        print(f"    {key:<12} {value}")
    print(f"  genomes        {data['genomes']}")
    print(f"  organisms      {data['organisms']}")
    print(f"  publications   {data['publications']}")
    print(f"  seq-pub links  {data['sequence_links']}")
    print(f"  duplicate keys {data['duplicate_keys']}")
    print("  sources:")
    for key, value in sorted((data.get("by_source") or {}).items()):
        print(f"    {key:<16} {value}")


async def main() -> None:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sequences-only", action="store_true")
    parser.add_argument("--pubmed-only", action="store_true")
    parser.add_argument("--skip-fill", action="store_true")
    args = parser.parse_args()

    checkpoint = _load_checkpoint()
    before = await snapshot()
    if checkpoint.get("before") is None:
        checkpoint["before"] = before
        _save_checkpoint(checkpoint)
    _print_snapshot("DATASET BEFORE (this process)", before)

    seq_report = ImportReport()
    pub_report = ImportReport()

    if not args.pubmed_only:
        print("\n--- sequence expansion (first pass) ---")
        _merge(seq_report, await run_sequence_jobs(checkpoint, SEQUENCE_JOBS))
        stats = await snapshot()
        if stats["sequences"] < SEQUENCE_TARGET and not args.skip_fill:
            print("\n--- sequence fill (second pass) ---")
            _merge(seq_report, await run_sequence_jobs(checkpoint, FILL_JOBS))
        stats = await snapshot()
        if stats["sequences"] < SEQUENCE_TARGET and not args.skip_fill:
            print("\n--- sequence extra pass ---")
            _merge(seq_report, await run_sequence_jobs(checkpoint, EXTRA_JOBS))
        stats = await snapshot()
        if stats["sequences"] < SEQUENCE_TARGET and not args.skip_fill:
            print("\n--- sequence extra pass 2 ---")
            _merge(seq_report, await run_sequence_jobs(checkpoint, EXTRA2_JOBS))

    if not args.sequences_only:
        print("\n--- PubMed expansion ---")
        _merge(pub_report, await run_pubmed(checkpoint))

    print("\n--- refresh counters / integrity ---")
    sync_info = await refresh_and_integrity()
    print(json.dumps(sync_info["refreshed"], indent=2))
    print("integrity ok:", sync_info["integrity"].get("ok"))

    after = await snapshot()
    checkpoint["after"] = after
    checkpoint["sequence_report"] = seq_report.as_dict()
    checkpoint["publication_report"] = pub_report.as_dict()
    _save_checkpoint(checkpoint)
    _print_snapshot("DATASET AFTER", after)

    before_saved = checkpoint.get("before") or before
    print("\n" + "=" * 64)
    print("EXPANSION DELTA")
    print("=" * 64)
    print(f"  sequences      {before_saved['sequences']} -> {after['sequences']}  (+{after['sequences'] - before_saved['sequences']})")
    print(f"  publications   {before_saved['publications']} -> {after['publications']}  (+{after['publications'] - before_saved['publications']})")
    print(f"  organisms      {before_saved['organisms']} -> {after['organisms']}")
    print(f"  genomes        {before_saved['genomes']} -> {after['genomes']}")
    print(f"  skipped        {seq_report.skipped + pub_report.skipped}")
    print(f"  failed         {seq_report.failed + pub_report.failed}")
    print(f"  checkpoint     {CHECKPOINT_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
