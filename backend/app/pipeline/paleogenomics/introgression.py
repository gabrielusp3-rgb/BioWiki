"""Curated archaic-introgression loci in living Homo sapiens.

Gene-level records from peer-reviewed papers. Coordinates are omitted unless
a cited paper plus genome build is stored — this catalogue does not invent
intervals. These rows are not ancient specimen DNA.
"""

from __future__ import annotations

from app.pipeline.paleogenomics import citations as C
from app.pipeline.paleogenomics.catalogue import HOMO_SAPIENS_TAX_ID

INTROGRESSION_LOCI: tuple[dict[str, object], ...] = (
    {
        "archaic_source": "neanderthal",
        "gene_name": "BNC2",
        "locus_name": "BNC2 pigmentation-associated interval",
        "pubmed_id": C.SANKARARAMAN_2014_NEANDERTHAL_ANCESTRY,
        "method": "published scan of Neanderthal ancestry in present-day humans",
        "evidence_notes": (
            "Sankararaman et al. 2014 reported widespread Neanderthal ancestry in "
            "non-African genomes, including intervals overlapping BNC2. Ancestry "
            "proportion is an estimate that varies by individual, population and method; "
            "it is not a fixed racial percentage. Coordinates are not copied here because "
            "this catalogue does not invent genome-build intervals."
        ),
        "source_dataset": "Sankararaman et al. 2014 Nature PMID 24476815",
    },
    {
        "archaic_source": "neanderthal",
        "gene_name": "OAS1",
        "locus_name": "OAS antiviral locus",
        "pubmed_id": C.SANKARARAMAN_2014_NEANDERTHAL_ANCESTRY,
        "method": "published Neanderthal ancestry scan",
        "evidence_notes": (
            "Innate-immunity OAS genes are among loci reported in ancestry scans of "
            "present-day humans. This row records the gene-level published association, "
            "not a bone-derived Neanderthal sequence."
        ),
        "source_dataset": "Sankararaman et al. 2014 Nature PMID 24476815",
    },
    {
        "archaic_source": "neanderthal",
        "gene_name": "POU2F3",
        "locus_name": "POU2F3",
        "pubmed_id": C.SANKARARAMAN_2014_NEANDERTHAL_ANCESTRY,
        "method": "published Neanderthal ancestry scan",
        "evidence_notes": (
            "POU2F3 is among loci discussed in the 2014 genomic landscape of Neanderthal "
            "ancestry. Gene-level only; no invented coordinates."
        ),
        "source_dataset": "Sankararaman et al. 2014 Nature PMID 24476815",
    },
    {
        "archaic_source": "neanderthal",
        "gene_name": "HYAL2",
        "locus_name": "HYAL2",
        "pubmed_id": C.SANKARARAMAN_2014_NEANDERTHAL_ANCESTRY,
        "method": "published Neanderthal ancestry scan",
        "evidence_notes": (
            "HYAL2 is among loci reported in Neanderthal-ancestry maps of living humans."
        ),
        "source_dataset": "Sankararaman et al. 2014 Nature PMID 24476815",
    },
    {
        "archaic_source": "neanderthal",
        "gene_name": "STAT2",
        "locus_name": "STAT2 haplotype",
        "pubmed_id": C.MENDEZ_2012_STAT2,
        "method": "haplotype sharing with Neanderthal genomes",
        "evidence_notes": (
            "Mendez et al. 2012 described a STAT2 haplotype in some modern humans "
            "inferred to derive from Neanderthals and as a candidate of positive "
            "selection in Papua New Guinea. This is introgression inference in "
            "Homo sapiens, not a Neanderthal specimen sequence."
        ),
        "source_dataset": "Mendez et al. 2012 Am J Hum Genet PMID 22883142",
    },
    {
        "archaic_source": "neanderthal",
        "gene_name": "TLR1",
        "locus_name": "TLR1 innate-immunity cluster",
        "pubmed_id": C.DESCHAMPS_2016_INNATE_IMMUNITY,
        "method": "scan of archaic introgression at innate-immunity genes",
        "evidence_notes": (
            "Deschamps et al. 2016 reported genomic signatures of introgression from "
            "archaic hominins at human innate-immunity genes, including Toll-like "
            "receptor loci. Modern carriers are Homo sapiens."
        ),
        "source_dataset": "Deschamps et al. 2016 Am J Hum Genet PMID 26748513",
    },
    {
        "archaic_source": "neanderthal",
        "gene_name": "TLR6",
        "locus_name": "TLR6 innate-immunity cluster",
        "pubmed_id": C.DESCHAMPS_2016_INNATE_IMMUNITY,
        "method": "scan of archaic introgression at innate-immunity genes",
        "evidence_notes": (
            "TLR6 is part of the TLR1/TLR6/TLR10 cluster discussed in archaic-introgression "
            "scans of innate immunity. Not a Neanderthal bone sequence."
        ),
        "source_dataset": "Deschamps et al. 2016 Am J Hum Genet PMID 26748513",
    },
    {
        "archaic_source": "neanderthal",
        "gene_name": "TLR10",
        "locus_name": "TLR10 innate-immunity cluster",
        "pubmed_id": C.DESCHAMPS_2016_INNATE_IMMUNITY,
        "method": "scan of archaic introgression at innate-immunity genes",
        "evidence_notes": (
            "TLR10 is part of the same innate-immunity cluster. Evidence is population-genetic, "
            "not a museum specimen."
        ),
        "source_dataset": "Deschamps et al. 2016 Am J Hum Genet PMID 26748513",
    },
    {
        "archaic_source": "denisovan",
        "gene_name": "EPAS1",
        "locus_name": "EPAS1 high-altitude haplotype",
        "pubmed_id": C.HUERTA_SANCHEZ_2014_EPAS1,
        "method": "population-genetic match to the Denisovan genome",
        "evidence_notes": (
            "Huerta-Sánchez et al. 2014 reported that a Denisovan-like EPAS1 haplotype "
            "is associated with high-altitude adaptation in Tibetans. The modern carriers "
            "are Homo sapiens; the archaic source is Denisovan, not Neanderthal."
        ),
        "source_dataset": "Huerta-Sánchez et al. 2014 Nature PMID 25043035",
    },
)


def introgression_modern_tax_id() -> int:
    return HOMO_SAPIENS_TAX_ID
