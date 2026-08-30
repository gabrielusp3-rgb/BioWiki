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
            "present-day humans (Sankararaman et al. 2014). Zhou et al. 2021 (PMID "
            "33633408) further reported a Neanderthal OAS1 isoform associated with "
            "COVID-19 susceptibility/severity in people of European ancestry. This row "
            "is gene-level introgression inference in Homo sapiens, not a bone-derived "
            "Neanderthal sequence. Coordinates are omitted."
        ),
        "source_dataset": "Sankararaman et al. 2014 Nature PMID 24476815; Zhou et al. 2021 PNAS PMID 33633408",
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
    {
        "archaic_source": "neanderthal",
        "gene_name": "LZTFL1",
        "locus_name": "3p21.31 COVID-19 risk haplotype (LZTFL1 region)",
        "pubmed_id": C.ZEBERG_2020_COVID_RISK_HAPLOTYPE,
        "method": "haplotype sharing with the Vindija Neanderthal genome",
        "evidence_notes": (
            "Zeberg and Pääbo 2020 reported that a 3p21.31 haplotype associated with "
            "risk of severe COVID-19 is inherited from Neanderthals. Several genes "
            "overlap that haplotype; LZTFL1 is recorded here as the named gene-level "
            "entry. This is ancestry in living Homo sapiens, not DNA extracted from a "
            "Neanderthal specimen. Coordinates are omitted because this catalogue does "
            "not invent genome-build intervals."
        ),
        "source_dataset": "Zeberg and Pääbo 2020 Nature PMID 32998156",
    },
    {
        "archaic_source": "denisovan",
        "gene_name": "WARS2",
        "locus_name": "WARS2 Denisovan-ancestry interval",
        "pubmed_id": C.SANKARARAMAN_2016_COMBINED_LANDSCAPE,
        "method": "published scan of Denisovan ancestry in present-day humans",
        "evidence_notes": (
            "Sankararaman et al. 2016 mapped Denisovan ancestry in present-day humans "
            "and reported WARS2 among high-ranking Denisovan-ancestry loci, particularly "
            "in Oceanian populations. Modern carriers are Homo sapiens. Gene-level only; "
            "no invented coordinates."
        ),
        "source_dataset": "Sankararaman et al. 2016 Curr Biol PMID 27032491",
    },
)


def introgression_modern_tax_id() -> int:
    return HOMO_SAPIENS_TAX_ID
