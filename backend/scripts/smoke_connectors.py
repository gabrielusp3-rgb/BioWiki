"""Smoke test: every connector's standardised find() against the real APIs.

Run:  python -m scripts.smoke_connectors
Uses only real, well-known identifiers (human insulin INS, PDB 4INS, RF00005).
"""

from __future__ import annotations

import asyncio

from app.services.connectors import (
    ENAConnector,
    EnsemblConnector,
    GenBankConnector,
    NCBIConnector,
    PDBConnector,
    PubMedConnector,
    RefSeqConnector,
    RfamConnector,
    SourceQuery,
    UniProtConnector,
)


def show(name: str, page) -> None:
    ids = [h.identifier for h in page.hits[:5]]
    print(f"{name:<28} source={page.source:<8} total={page.total} "
          f"next={page.next_cursor} hits={ids}")


async def main() -> None:
    q_gene = SourceQuery(gene="INS", organism="Homo sapiens", sequence_type="rna", limit=5)

    async with NCBIConnector() as ncbi:
        show("ncbi gene+organism+rna", await ncbi.find(q_gene))
        show("ncbi pubmed_id=3313277", await ncbi.find(SourceQuery(pubmed_id=3313277, limit=5)))

    async with GenBankConnector() as genbank:
        show("genbank accession", await genbank.find(SourceQuery(accession="NM_000207", limit=5)))

    async with RefSeqConnector() as refseq:
        show("refseq gene+organism", await refseq.find(q_gene))

    async with UniProtConnector() as uniprot:
        show("uniprot gene+organism", await uniprot.find(
            SourceQuery(gene="INS", organism="Homo sapiens", sequence_type="protein", limit=5)
        ))

    async with EnsemblConnector() as ensembl:
        show("ensembl gene+organism", await ensembl.find(
            SourceQuery(gene="INS", organism="Homo sapiens")
        ))

    async with PDBConnector() as pdb:
        show("pdb accession=4INS", await pdb.find(SourceQuery(accession="4INS", limit=5)))
        show("pdb gene+organism", await pdb.find(
            SourceQuery(gene="INS", organism="Homo sapiens", limit=5)
        ))

    async with ENAConnector() as ena:
        show("ena accession", await ena.find(SourceQuery(accession="J00265", limit=5)))

    async with RfamConnector() as rfam:
        show("rfam RF00005 (tRNA)", await rfam.find(SourceQuery(accession="RF00005")))

    async with PubMedConnector() as pubmed:
        show("pubmed gene+organism", await pubmed.find(
            SourceQuery(gene="insulin", organism="Homo sapiens", limit=5)
        ))
        articles = await pubmed.fetch_articles([3313277], with_abstracts=True)
        for a in articles:
            has_abstract = bool(a.abstract)
            print(f"pubmed article {a.pubmed_id}: {a.title!r} ({a.year}) "
                  f"journal={a.journal!r} authors={len(a.authors)} "
                  f"abstract={'yes, ' + str(len(a.abstract)) + ' chars' if has_abstract else 'none at source'} "
                  f"url={a.source_url}")


if __name__ == "__main__":
    asyncio.run(main())
