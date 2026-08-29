"""Biodiversity-first candidate plan. Limits are computed from CLI targets."""

from __future__ import annotations

from typing import Any

# Midpoints of the guidance bands (quality still wins over filling a %).
CATEGORY_SHARES = {
    "dna": 0.25,
    "rna": 0.20,
    "protein": 0.30,
    "virus": 0.12,
    "crispr": 0.10,
}

# Bulk inclusion caps. Larger authentic records are skipped, never truncated.
DEFAULT_MAX_LENGTHS = {
    "dna": 50_000,
    "rna": 25_000,
    "protein": 8_000,
    "peptide": 120,
    "virus": 300_000,
    "crispr": 50_000,
}

_DNA_SLEN = "600:25000[SLEN]"
_RNA_SLEN = "200:12000[SLEN]"
_VIRUS_SLEN = "800:250000[SLEN]"
_CRISPR_SLEN = "200:40000[SLEN]"

# Computational Cas9 NGG examples: model organisms, plants, paleogenomics.
# Not used for high-risk pathogen design campaigns.
COMPUTATIONAL_TAX_IDS: dict[int, str] = {
    3702: "Arabidopsis thaliana",
    4932: "Saccharomyces cerevisiae",
    559292: "Saccharomyces cerevisiae S288C",
    6239: "Caenorhabditis elegans",
    7227: "Drosophila melanogaster",
    7955: "Danio rerio",
    9031: "Gallus gallus",
    4577: "Zea mays",
    4081: "Solanum lycopersicum",
    37349: "Mammuthus primigenius",
}

# (scientific name, tax_id, organism group)
ANIMALS: list[tuple[str, int, str]] = [
    ("Homo sapiens", 9606, "animal"),
    ("Mus musculus", 10090, "animal"),
    ("Rattus norvegicus", 10116, "animal"),
    ("Pan troglodytes", 9598, "animal"),
    ("Bos taurus", 9913, "animal"),
    ("Sus scrofa", 9823, "animal"),
    ("Canis lupus familiaris", 9615, "animal"),
    ("Felis catus", 9685, "animal"),
    ("Loxodonta africana", 9785, "animal"),
    ("Elephas maximus", 9783, "animal"),
    ("Mammuthus primigenius", 37349, "animal"),
    ("Equus caballus", 9796, "animal"),
    ("Ovis aries", 9940, "animal"),
    ("Oryctolagus cuniculus", 9986, "animal"),
    ("Macaca mulatta", 9544, "animal"),
    ("Gallus gallus", 9031, "animal"),
    ("Taeniopygia guttata", 59729, "animal"),
    ("Anas platyrhynchos", 8839, "animal"),
    ("Meleagris gallopavo", 9103, "animal"),
    ("Danio rerio", 7955, "animal"),
    ("Oryzias latipes", 8090, "animal"),
    ("Salmo salar", 8030, "animal"),
    ("Takifugu rubripes", 31033, "animal"),
    ("Gasterosteus aculeatus", 69293, "animal"),
    ("Xenopus tropicalis", 8364, "animal"),
    ("Ambystoma mexicanum", 8296, "animal"),
    ("Anolis carolinensis", 28377, "animal"),
    ("Python bivittatus", 176946, "animal"),
    ("Chrysemys picta", 8478, "animal"),
    ("Pelodiscus sinensis", 13735, "animal"),
    ("Drosophila melanogaster", 7227, "animal"),
    ("Anopheles gambiae", 7165, "animal"),
    ("Apis mellifera", 7460, "animal"),
    ("Bombyx mori", 7091, "animal"),
    ("Tribolium castaneum", 7070, "animal"),
    ("Aedes aegypti", 7159, "animal"),
    ("Caenorhabditis elegans", 6239, "animal"),
    ("Schistosoma mansoni", 6183, "animal"),
    ("Strongylocentrotus purpuratus", 7668, "animal"),
    ("Nematostella vectensis", 45351, "animal"),
    ("Amphimedon queenslandica", 400682, "animal"),
    ("Octopus vulgaris", 6645, "animal"),
    ("Crassostrea gigas", 29159, "animal"),
    ("Xenopus laevis", 8355, "animal"),
    ("Ciona intestinalis", 7719, "animal"),
    ("Branchiostoma floridae", 7739, "animal"),
    ("Petromyzon marinus", 7757, "animal"),
    ("Ornithorhynchus anatinus", 9258, "animal"),
    ("Monodelphis domestica", 13616, "animal"),
    ("Hydra vulgaris", 6087, "animal"),
    ("Daphnia pulex", 6669, "animal"),
    ("Ixodes scapularis", 6945, "animal"),
    ("Aplysia californica", 6500, "animal"),
    ("Helobdella robusta", 6412, "animal"),
    ("Capitella teleta", 283909, "animal"),
]

PLANTS: list[tuple[str, int, str]] = [
    ("Arabidopsis thaliana", 3702, "plant"),
    ("Oryza sativa", 4530, "plant"),
    ("Zea mays", 4577, "plant"),
    ("Solanum lycopersicum", 4081, "plant"),
    ("Glycine max", 3847, "plant"),
    ("Triticum aestivum", 4565, "plant"),
    ("Hordeum vulgare", 4513, "plant"),
    ("Solanum tuberosum", 4113, "plant"),
    ("Vitis vinifera", 29760, "plant"),
    ("Populus trichocarpa", 3694, "plant"),
    ("Nicotiana tabacum", 4097, "plant"),
    ("Physcomitrium patens", 3218, "plant"),
    ("Selaginella moellendorffii", 88036, "plant"),
    ("Pinus taeda", 3352, "plant"),
    ("Chlamydomonas reinhardtii", 3055, "plant"),
    ("Cyanidioschyzon merolae", 45157, "plant"),
    ("Medicago truncatula", 3880, "plant"),
    ("Brassica rapa", 3711, "plant"),
    ("Sorghum bicolor", 4558, "plant"),
    ("Cucumis sativus", 3659, "plant"),
    ("Malus domestica", 3750, "plant"),
    ("Theobroma cacao", 3641, "plant"),
    ("Marchantia polymorpha", 3197, "plant"),
    ("Volvox carteri", 3067, "plant"),
    ("Porphyra umbilicalis", 2788, "plant"),
]

FUNGI: list[tuple[str, int, str]] = [
    ("Saccharomyces cerevisiae", 4932, "fungus"),
    ("Schizosaccharomyces pombe", 4896, "fungus"),
    ("Neurospora crassa", 5141, "fungus"),
    ("Aspergillus nidulans", 162425, "fungus"),
    ("Aspergillus fumigatus", 746128, "fungus"),
    ("Candida albicans", 5476, "fungus"),
    ("Cryptococcus neoformans", 5207, "fungus"),
    ("Ustilago maydis", 237631, "fungus"),
    ("Phanerochaete chrysosporium", 5306, "fungus"),
    ("Yarrowia lipolytica", 4952, "fungus"),
    ("Pichia pastoris", 4922, "fungus"),
    ("Fusarium graminearum", 5518, "fungus"),
    ("Coprinopsis cinerea", 5346, "fungus"),
    ("Batrachochytrium dendrobatidis", 109871, "fungus"),
    ("Rhizopus oryzae", 64495, "fungus"),
    ("Laccaria bicolor", 29883, "fungus"),
]

PROTISTS: list[tuple[str, int, str]] = [
    ("Plasmodium falciparum", 5833, "protozoan"),
    ("Plasmodium vivax", 5855, "protozoan"),
    ("Trypanosoma brucei", 5691, "protozoan"),
    ("Trypanosoma cruzi", 5693, "protozoan"),
    ("Leishmania major", 5664, "protozoan"),
    ("Toxoplasma gondii", 5811, "protozoan"),
    ("Tetrahymena thermophila", 5911, "protozoan"),
    ("Paramecium tetraurelia", 5888, "protozoan"),
    ("Dictyostelium discoideum", 44689, "protozoan"),
    ("Giardia intestinalis", 5741, "protozoan"),
    ("Entamoeba histolytica", 5759, "protozoan"),
    ("Phytophthora infestans", 4787, "protozoan"),
    ("Emiliania huxleyi", 2903, "protozoan"),
    ("Naegleria gruberi", 5762, "protozoan"),
    ("Thalassiosira pseudonana", 35128, "protozoan"),
    ("Bigelowiella natans", 227086, "protozoan"),
    ("Trichomonas vaginalis", 5722, "protozoan"),
    ("Cryptosporidium parvum", 5807, "protozoan"),
]

BACTERIA: list[tuple[str, int, str]] = [
    ("Escherichia coli", 562, "bacteria"),
    ("Bacillus subtilis", 1423, "bacteria"),
    ("Pseudomonas aeruginosa", 287, "bacteria"),
    ("Streptomyces coelicolor", 1902, "bacteria"),
    ("Mycobacterium smegmatis", 1772, "bacteria"),
    ("Vibrio fischeri", 668, "bacteria"),
    ("Staphylococcus aureus", 1280, "bacteria"),
    ("Streptococcus pyogenes", 1314, "bacteria"),
    ("Streptococcus thermophilus", 1308, "bacteria"),
    ("Salmonella enterica", 28901, "bacteria"),
    ("Listeria monocytogenes", 1639, "bacteria"),
    ("Helicobacter pylori", 210, "bacteria"),
    ("Synechocystis sp. PCC 6803", 1148, "bacteria"),
    ("Prochlorococcus marinus", 1219, "bacteria"),
    ("Bacteroides thetaiotaomicron", 818, "bacteria"),
    ("Caulobacter crescentus", 155892, "bacteria"),
    ("Agrobacterium tumefaciens", 358, "bacteria"),
    ("Rhizobium leguminosarum", 384, "bacteria"),
    ("Deinococcus radiodurans", 1299, "bacteria"),
    ("Thermus thermophilus", 274, "bacteria"),
    ("Lactobacillus acidophilus", 1579, "bacteria"),
    ("Lactococcus lactis", 1358, "bacteria"),
    ("Clostridium acetobutylicum", 1488, "bacteria"),
    ("Myxococcus xanthus", 34, "bacteria"),
    ("Aquifex aeolicus", 63363, "bacteria"),
    ("Borrelia burgdorferi", 139, "bacteria"),
    ("Chlamydia trachomatis", 813, "bacteria"),
    ("Neisseria meningitidis", 487, "bacteria"),
    ("Haemophilus influenzae", 727, "bacteria"),
    ("Corynebacterium glutamicum", 1718, "bacteria"),
    ("Bradyrhizobium japonicum", 375, "bacteria"),
    ("Rhodobacter sphaeroides", 1063, "bacteria"),
    ("Synechococcus elongatus", 32046, "bacteria"),
    ("Anabaena sp. PCC 7120", 103690, "bacteria"),
    ("Planctopirus limnophila", 125, "bacteria"),
    ("Chloroflexus aurantiacus", 1108, "bacteria"),
    ("Thermotoga maritima", 2336, "bacteria"),
    ("Geobacter sulfurreducens", 35554, "bacteria"),
    ("Shewanella oneidensis", 70863, "bacteria"),
    ("Xanthomonas campestris", 339, "bacteria"),
    ("Erwinia amylovora", 552, "bacteria"),
    ("Paenibacillus polymyxa", 1406, "bacteria"),
    ("Frankia alni", 106370, "bacteria"),
    ("Nostoc punctiforme", 272131, "bacteria"),
    ("Bifidobacterium longum", 216816, "bacteria"),
    ("Enterococcus faecalis", 1351, "bacteria"),
    ("Acidithiobacillus ferrooxidans", 920, "bacteria"),
    ("Nitrosomonas europaea", 915, "bacteria"),
    ("Flavobacterium johnsoniae", 986, "bacteria"),
    ("Chlorobium tepidum", 1097, "bacteria"),
    ("Gemmata obscuriglobus", 36818, "bacteria"),
    ("Mesorhizobium loti", 381, "bacteria"),
]

ARCHAEA: list[tuple[str, int, str]] = [
    ("Methanocaldococcus jannaschii", 2190, "archaea"),
    ("Methanosarcina acetivorans", 2214, "archaea"),
    ("Methanothermobacter thermautotrophicus", 145262, "archaea"),
    ("Haloferax volcanii", 2246, "archaea"),
    ("Halobacterium salinarum", 2242, "archaea"),
    ("Saccharolobus solfataricus", 2287, "archaea"),
    ("Saccharolobus islandicus", 43080, "archaea"),
    ("Pyrococcus furiosus", 2261, "archaea"),
    ("Thermococcus kodakarensis", 69014, "archaea"),
    ("Archaeoglobus fulgidus", 2234, "archaea"),
    ("Nanoarchaeum equitans", 228908, "archaea"),
    ("Thermoplasma acidophilum", 2303, "archaea"),
    ("Nitrosopumilus maritimus", 436308, "archaea"),
    ("Pyrobaculum aerophilum", 13773, "archaea"),
    ("Sulfolobus acidocaldarius", 2285, "archaea"),
    ("Haloarcula marismortui", 2238, "archaea"),
    ("Methanococcus maripaludis", 39152, "archaea"),
    ("Ignicoccus hospitalis", 12989, "archaea"),
    ("Methanopyrus kandleri", 2326, "archaea"),
    ("Ferroplasma acidarmanus", 144129, "archaea"),
    ("Cenarchaeum symbiosum", 41404, "archaea"),
    ("Pyrococcus abyssi", 29292, "archaea"),
    ("Methanospirillum hungatei", 145411, "archaea"),
]

VIRUS_FAMILIES: list[tuple[str, str]] = [
    ("Caudoviricetes", "phage"),
    ("Herpesviridae", "dsDNA"),
    ("Papillomaviridae", "dsDNA"),
    ("Adenoviridae", "dsDNA"),
    ("Poxviridae", "dsDNA"),
    ("Circoviridae", "ssDNA"),
    ("Geminiviridae", "ssDNA"),
    ("Parvoviridae", "ssDNA"),
    ("Microviridae", "ssDNA"),
    ("Reoviridae", "dsRNA"),
    ("Totiviridae", "dsRNA"),
    ("Picornaviridae", "ssRNA+"),
    ("Flaviviridae", "ssRNA+"),
    ("Potyviridae", "ssRNA+"),
    ("Tymoviridae", "ssRNA+"),
    ("Coronaviridae", "ssRNA+"),
    ("Togaviridae", "ssRNA+"),
    ("Rhabdoviridae", "ssRNA-"),
    ("Orthomyxoviridae", "ssRNA-"),
    ("Paramyxoviridae", "ssRNA-"),
    ("Bunyavirales", "ssRNA-"),
    ("Retroviridae", "ssRNA-RT"),
    ("Hepadnaviridae", "dsDNA-RT"),
    ("Caulimoviridae", "dsDNA-RT"),
    ("Fuselloviridae", "archaeal"),
    ("Rudiviridae", "archaeal"),
    ("Leviviridae", "rna-phage"),
    ("Tectiviridae", "phage"),
    ("Inoviridae", "phage"),
    ("Iridoviridae", "dsDNA"),
    ("Polyomaviridae", "dsDNA"),
    ("Anelloviridae", "ssDNA"),
    ("Partitiviridae", "dsRNA"),
    ("Tombusviridae", "ssRNA+"),
    ("Bromoviridae", "ssRNA+"),
    ("Caliciviridae", "ssRNA+"),
    ("Nodaviridae", "ssRNA+"),
    ("Astroviridae", "ssRNA+"),
    ("Phycodnaviridae", "dsDNA"),
    ("Mimiviridae", "dsDNA"),
    ("Picobirnaviridae", "dsRNA"),
]

RFAM_FAMILIES: list[tuple[str, str, int]] = [
    ("RF00001", "5S rRNA", 12),
    ("RF00002", "5.8S rRNA", 8),
    ("RF00003", "U1", 8),
    ("RF00004", "U2", 8),
    ("RF00005", "tRNA", 16),
    ("RF00007", "U12", 6),
    ("RF00026", "U6", 8),
    ("RF00177", "bacterial SSU rRNA", 10),
    ("RF00010", "RNase P", 8),
    ("RF00008", "Hammerhead", 6),
    ("RF00162", "SAM riboswitch", 6),
    ("RF00059", "TPP riboswitch", 6),
    ("RF00013", "6S RNA", 6),
    ("RF00017", "SRP RNA", 6),
    ("RF00020", "U5 spliceosomal", 6),
    ("RF00050", "FMN riboswitch", 6),
    ("RF00167", "Purine riboswitch", 6),
    ("RF00234", "glmS ribozyme", 6),
]

PDB_IDS: list[str] = [
    "4HHB", "1BNA", "1EHZ", "1MBO", "1INS", "2LYZ", "1UBQ", "1CRN",
    "3CLN", "1GFL", "1AKE", "1TIM", "1MBN", "5P21", "1PGA", "1HHO",
    "2HHB", "3NIR", "1L2Y", "1AKG", "1GZX", "4INS", "3TGI", "1LYZ",
    "1BTL", "1HHO", "2CTC", "1RIE", "1C3W", "1FBB",
]

PUBMED_SEARCHES: list[tuple[str, str, int]] = [
    ("pm-crispr", "CRISPR[Title] AND (Cas9[Title] OR Cas12[Title] OR Cas13[Title])", 400),
    ("pm-crispr-archaea", "CRISPR[Title] AND (Archaea[Title] OR Haloferax[Title] OR Sulfolobus[Title])", 200),
    ("pm-tp53", "TP53[Title] AND (mutation[Title] OR genome[Title]) AND humans[MeSH]", 250),
    ("pm-brca", "(BRCA1[Title] OR BRCA2[Title]) AND (cancer[Title] OR genome[Title])", 250),
    ("pm-insulin", "insulin[Title] AND (gene[Title] OR receptor[Title]) AND humans[MeSH]", 200),
    ("pm-egfr", "EGFR[Title] AND (mutation[Title] OR inhibitor[Title])", 200),
    ("pm-sars2", "SARS-CoV-2[Title] AND (spike[Title] OR genome[Title])", 300),
    ("pm-influenza", "influenza[Title] AND (hemagglutinin[Title] OR genome[Title])", 200),
    ("pm-hiv", "HIV-1[Title] AND (genome[Title] OR envelope[Title])", 150),
    ("pm-ecoli", "Escherichia coli[Title] AND (genome[Title] OR CRISPR[Title])", 200),
    ("pm-bacillus", "Bacillus subtilis[Title] AND genome[Title]", 120),
    ("pm-streptomyces", "Streptomyces[Title] AND (genome[Title] OR CRISPR[Title])", 120),
    ("pm-cyanobacteria", "(Synechocystis[Title] OR Prochlorococcus[Title]) AND genome[Title]", 80),
    ("pm-arabidopsis", "Arabidopsis thaliana[Title] AND (genome[Title] OR gene[Title])", 250),
    ("pm-rice", "Oryza sativa[Title] AND (genome[Title] OR gene[Title])", 150),
    ("pm-maize", "Zea mays[Title] AND (genome[Title] OR gene[Title])", 120),
    ("pm-drosophila", "Drosophila melanogaster[Title] AND (genome[Title] OR development[Title])", 200),
    ("pm-zebrafish", "Danio rerio[Title] AND (genome[Title] OR development[Title])", 150),
    ("pm-yeast", "Saccharomyces cerevisiae[Title] AND (genome[Title] OR gene[Title])", 200),
    ("pm-plasmodium", "Plasmodium falciparum[Title] AND (genome[Title] OR vaccine[Title])", 150),
    ("pm-trypanosoma", "Trypanosoma[Title] AND genome[Title]", 80),
    ("pm-xenopus", "Xenopus[Title] AND (genome[Title] OR development[Title])", 80),
    ("pm-chicken", "Gallus gallus[Title] AND (genome[Title] OR gene[Title])", 80),
    ("pm-anole", "Anolis carolinensis[Title] AND genome[Title]", 40),
    ("pm-axolotl", "Ambystoma mexicanum[Title] AND (genome[Title] OR regeneration[Title])", 60),
    ("pm-archaea", "Archaea[Title] AND (CRISPR[Title] OR genome[Title])", 150),
    ("pm-rfam", "(noncoding RNA[Title] OR Rfam[Title]) AND (ribosome[Title] OR family[Title])", 120),
    ("pm-pdb", "protein structure[Title] AND (crystallography[Title] OR PDB[Title])", 150),
    ("pm-mammoth", "(Mammuthus primigenius[Title] OR woolly mammoth[Title]) AND (genome[Title] OR DNA[Title])", 80),
    ("pm-paleogenomics", "(ancient DNA[Title] OR paleogenomics[Title] OR palaeogenomics[Title])", 200),
    ("pm-chloroplast", "chloroplast[Title] AND (genome[Title] OR gene[Title])", 120),
    ("pm-mitochondrial", "mitochondrial DNA[Title] AND (genome[Title] OR phylogeny[Title])", 150),
    ("pm-phage", "(bacteriophage[Title] OR Caudovirales[Title]) AND genome[Title]", 150),
    ("pm-plant-virus", "(Potyvirus[Title] OR Geminivirus[Title]) AND genome[Title]", 80),
    ("pm-rna-family", "(rRNA[Title] OR tRNA[Title] OR lncRNA[Title] OR microRNA[Title]) AND (genome[Title] OR family[Title])", 200),
    ("pm-uniprot", "UniProt[Title] AND (annotation[Title] OR proteome[Title])", 80),
    ("pm-elephant", "(Loxodonta africana[Title] OR Elephas maximus[Title]) AND (genome[Title] OR DNA[Title])", 60),
    ("pm-canis", "Canis lupus[Title] AND (genome[Title] OR gene[Title])", 80),
    ("pm-felis", "Felis catus[Title] AND (genome[Title] OR gene[Title])", 60),
    ("pm-bos", "Bos taurus[Title] AND (genome[Title] OR gene[Title])", 80),
    ("pm-wheat", "Triticum aestivum[Title] AND (genome[Title] OR gene[Title])", 80),
    ("pm-soybean", "Glycine max[Title] AND (genome[Title] OR gene[Title])", 80),
    ("pm-tomato", "Solanum lycopersicum[Title] AND (genome[Title] OR gene[Title])", 60),
    ("pm-neurospora", "Neurospora crassa[Title] AND (genome[Title] OR gene[Title])", 60),
    ("pm-candida", "Candida albicans[Title] AND (genome[Title] OR gene[Title])", 80),
    ("pm-haloferax", "Haloferax[Title] AND (genome[Title] OR CRISPR[Title])", 60),
    ("pm-pyrococcus", "Pyrococcus[Title] AND (genome[Title] OR CRISPR[Title])", 60),
    ("pm-methanogen", "(Methanocaldococcus[Title] OR Methanosarcina[Title]) AND genome[Title]", 60),
    ("pm-cyanobacteria2", "(Anabaena[Title] OR Nostoc[Title] OR Synechococcus[Title]) AND genome[Title]", 80),
    ("pm-mycobacterium", "Mycobacterium smegmatis[Title] AND genome[Title]", 40),
    ("pm-pseudomonas", "Pseudomonas aeruginosa[Title] AND (genome[Title] OR CRISPR[Title])", 80),
    ("pm-cas12", "Cas12[Title] AND CRISPR[Title]", 150),
    ("pm-cas13", "Cas13[Title] AND CRISPR[Title]", 120),
    ("pm-rfam2", "(Rfam[Title] OR non-coding RNA[Title]) AND (family[Title] OR annotation[Title])", 80),
    ("pm-ensembl", "Ensembl[Title] AND (genome[Title] OR annotation[Title])", 80),
    ("pm-refseq", "RefSeq[Title] AND (annotation[Title] OR genome[Title])", 80),
    ("pm-chloroplast2", "(rbcL[Title] OR matK[Title]) AND (chloroplast[Title] OR plant[Title])", 80),
    ("pm-barcode", "(COI[Title] OR cox1[Title] OR DNA barcode[Title]) AND (taxonomy[Title] OR species[Title])", 120),
]


def _slug(name: str) -> str:
    return (
        name.lower()
        .replace(" ", "-")
        .replace(".", "")
        .replace("(", "")
        .replace(")", "")
        .replace("/", "-")[:40]
    )


def _limit(quota: int, n_jobs: int, *, min_n: int = 8, max_n: int = 42) -> int:
    if n_jobs <= 0:
        return min_n
    return max(min_n, min(max_n, max(1, quota // n_jobs)))


def _deprioritize_tax_ids(
    taxa: list[tuple[str, int, str]],
    later: set[int],
) -> list[tuple[str, int, str]]:
    """Keep job ids stable while avoiding model-organism-first ingestion."""
    head = [row for row in taxa if row[1] not in later]
    tail = [row for row in taxa if row[1] in later]
    return head + tail


def _dna_cds(organism: str) -> str:
    return (
        f'"{organism}"[Organism] AND biomol_genomic[PROP] AND '
        f'"complete cds"[Title] AND {_DNA_SLEN}'
    )


def _rna_mrna(organism: str) -> str:
    return (
        f'"{organism}"[Organism] AND biomol_mrna[PROP] AND refseq[filter] AND {_RNA_SLEN}'
    )


def _uniprot_reviewed(tax_id: int) -> str:
    return f"(organism_id:{tax_id}) AND (reviewed:true) AND (length:[60 TO 800])"


def _virus_complete(taxon: str) -> str:
    return (
        f'"{taxon}"[Organism] AND "complete genome"[Title] AND '
        f"srcdb_refseq[PROP] AND {_VIRUS_SLEN}"
    )


def _crispr_org(organism: str) -> str:
    return (
        f'CRISPR[Title] AND "{organism}"[Organism] AND {_CRISPR_SLEN}'
    )


def all_cellular_taxa() -> list[tuple[str, int, str]]:
    return ANIMALS + PLANTS + FUNGI + PROTISTS + BACTERIA + ARCHAEA


def build_sequence_jobs(
    additional_sequences: int,
    *,
    categories: set[str] | None = None,
    sources: set[str] | None = None,
) -> list[dict[str, Any]]:
    """Build a diversity-first job list. Limits scale with additional_sequences."""
    wanted = categories or set(CATEGORY_SHARES)
    src = sources or {
        "ncbi",
        "uniprot",
        "rfam",
        "pdb",
        "genomes",
    }
    extra = max(0, additional_sequences)
    # Fetch more candidates than the insert target: many hits already exist,
    # fail validation, or are skipped for length/diversity.
    oversample = 3.5
    jobs: list[dict[str, Any]] = []

    def allow(kind: str, category: str) -> bool:
        if category not in wanted and category != "genome":
            return False
        return kind in src or (kind == "genomes" and "genomes" in src)

    cellular = all_cellular_taxa()
    eukaryotes = [t for t in cellular if t[2] in {"animal", "plant", "fungus", "protozoan"}]
    prokaryotes = [t for t in cellular if t[2] in {"bacteria", "archaea"}]

    dna_quota = int(extra * CATEGORY_SHARES["dna"] * oversample)
    rna_quota = int(extra * CATEGORY_SHARES["rna"] * oversample)
    prot_quota = int(extra * CATEGORY_SHARES["protein"] * oversample)
    virus_quota = int(extra * CATEGORY_SHARES["virus"] * oversample)
    crispr_quota = int(extra * CATEGORY_SHARES["crispr"] * oversample)

    if allow("ncbi", "dna"):
        dna_limit = _limit(dna_quota, len(cellular), min_n=8, max_n=40)
        for name, tax_id, _group in cellular:
            jobs.append(
                {
                    "id": f"dna-{_slug(name)}",
                    "kind": "ncbi",
                    "term": _dna_cds(name),
                    "limit": dna_limit,
                    "seq_type": "dna",
                    "category": "dna",
                    "tax_id": tax_id,
                    "reason": "representative genomic CDS",
                }
            )
        jobs.extend(
            [
                {
                    "id": "dna-mt-chordata",
                    "kind": "ncbi",
                    "term": f'Chordata[Organism] AND mitochondrion[Filter] AND 14000:18000[SLEN]',
                    "limit": min(40, max(12, dna_quota // 40)),
                    "seq_type": "dna",
                    "category": "dna",
                    "reason": "mitochondrial DNA diversity",
                },
                {
                    "id": "dna-chloroplast",
                    "kind": "ncbi",
                    "term": 'Viridiplantae[Organism] AND chloroplast[Filter] AND biomol_genomic[PROP] AND 800:20000[SLEN]',
                    "limit": min(30, max(10, dna_quota // 40)),
                    "seq_type": "dna",
                    "category": "dna",
                    "reason": "chloroplast genes/regions within bulk length cap",
                },
                {
                    "id": "fill-dna-clades",
                    "kind": "ncbi",
                    "term": f'(Mammalia[Organism] OR Aves[Organism] OR Actinopterygii[Organism] OR Insecta[Organism] OR Viridiplantae[Organism] OR Fungi[Organism] OR Archaea[Organism]) AND biomol_genomic[PROP] AND "complete cds"[Title] AND {_DNA_SLEN}',
                    "limit": min(80, max(20, dna_quota // 8)),
                    "seq_type": "dna",
                    "category": "dna",
                    "reason": "clade-level fill after named taxa",
                },
                {
                    "id": "dna-cox1-metazoa",
                    "kind": "ncbi",
                    "term": "cox1[Gene] AND Metazoa[Organism] AND biomol_genomic[PROP] AND 500:1700[SLEN]",
                    "limit": min(160, max(40, dna_quota // 12)),
                    "seq_type": "dna",
                    "category": "dna",
                    "reason": "COI barcode diversity across animals",
                },
                {
                    "id": "dna-cytb-vertebrata",
                    "kind": "ncbi",
                    "term": "cytb[Gene] AND Vertebrata[Organism] AND biomol_genomic[PROP] AND 800:1300[SLEN]",
                    "limit": min(80, max(24, dna_quota // 20)),
                    "seq_type": "dna",
                    "category": "dna",
                    "reason": "cytochrome b vertebrate diversity",
                },
                {
                    "id": "dna-rbcl-plants",
                    "kind": "ncbi",
                    "term": "rbcL[Gene] AND Viridiplantae[Organism] AND biomol_genomic[PROP] AND 500:1600[SLEN]",
                    "limit": min(80, max(24, dna_quota // 20)),
                    "seq_type": "dna",
                    "category": "dna",
                    "reason": "rbcL plant barcode diversity",
                },
                {
                    "id": "dna-matk-plants",
                    "kind": "ncbi",
                    "term": "matK[Gene] AND Viridiplantae[Organism] AND biomol_genomic[PROP] AND 600:1600[SLEN]",
                    "limit": min(60, max(16, dna_quota // 24)),
                    "seq_type": "dna",
                    "category": "dna",
                    "reason": "matK plant barcode diversity",
                },
                {
                    "id": "dna-rpob-bacteria",
                    "kind": "ncbi",
                    "term": "rpoB[Gene] AND Bacteria[Organism] AND biomol_genomic[PROP] AND 800:4000[SLEN]",
                    "limit": min(80, max(24, dna_quota // 20)),
                    "seq_type": "dna",
                    "category": "dna",
                    "reason": "rpoB bacterial marker diversity",
                },
                {
                    "id": "dna-rpob-archaea",
                    "kind": "ncbi",
                    "term": "rpoB[Gene] AND Archaea[Organism] AND biomol_genomic[PROP] AND 800:4000[SLEN]",
                    "limit": min(40, max(12, dna_quota // 30)),
                    "seq_type": "dna",
                    "category": "dna",
                    "reason": "rpoB archaeal marker diversity",
                },
            ]
        )

    if allow("ncbi", "rna"):
        rna_euk_limit = _limit(int(rna_quota * 0.55), len(eukaryotes), min_n=6, max_n=28)
        for name, tax_id, _group in eukaryotes:
            jobs.append(
                {
                    "id": f"rna-{_slug(name)}",
                    "kind": "ncbi",
                    "term": _rna_mrna(name),
                    "limit": rna_euk_limit,
                    "seq_type": "rna",
                    "category": "rna",
                    "tax_id": tax_id,
                    "reason": "RefSeq mRNA",
                }
            )
        class_jobs = [
            (
                "rna-16s",
                '"16S ribosomal RNA"[Title] AND refseq[filter] AND 1200:1800[SLEN]',
                min(50, max(16, rna_quota // 12)),
            ),
            (
                "rna-23s",
                '"23S ribosomal RNA"[Title] AND refseq[filter] AND 2300:3200[SLEN]',
                min(24, max(8, rna_quota // 20)),
            ),
            (
                "rna-trna",
                '"tRNA"[Title] AND refseq[filter] AND 70:95[SLEN]',
                min(40, max(12, rna_quota // 16)),
            ),
            (
                "rna-lncrna",
                "biomol_ncrna[PROP] AND lncRNA[Title] AND refseq[filter] AND 200:12000[SLEN]",
                min(40, max(10, rna_quota // 16)),
            ),
            (
                "rna-mirna",
                "biomol_ncrna[PROP] AND microRNA[Title] AND refseq[filter] AND 60:150[SLEN]",
                min(30, max(8, rna_quota // 20)),
            ),
            (
                "rna-snrna",
                "biomol_ncrna[PROP] AND (U1[Title] OR U2[Title] OR U6[Title]) AND refseq[filter]",
                min(20, max(6, rna_quota // 30)),
            ),
            (
                "rna-18s",
                '"18S ribosomal RNA"[Title] AND refseq[filter] AND 1400:2000[SLEN]',
                min(40, max(12, rna_quota // 18)),
            ),
            (
                "rna-its-fungi",
                '"internal transcribed spacer"[Title] AND Fungi[Organism] AND 200:900[SLEN]',
                min(40, max(12, rna_quota // 18)),
            ),
            (
                "rna-16s-archaea",
                '"16S ribosomal RNA"[Title] AND Archaea[Organism] AND 1200:1800[SLEN]',
                min(30, max(10, rna_quota // 24)),
            ),
        ]
        for job_id, term, limit in class_jobs:
            jobs.append(
                {
                    "id": job_id,
                    "kind": "ncbi",
                    "term": term,
                    "limit": limit,
                    "seq_type": "rna",
                    "category": "rna",
                    "reason": "RNA class diversity",
                }
            )

    if allow("rfam", "rna"):
        for acc, label, base_limit in RFAM_FAMILIES:
            jobs.append(
                {
                    "id": f"rfam-{acc.lower()}",
                    "kind": "rfam",
                    "family": acc,
                    "limit": min(20, max(base_limit, rna_quota // 40)),
                    "category": "rna",
                    "reason": f"Rfam {label}",
                }
            )

    if allow("uniprot", "protein"):
        prot_limit = _limit(prot_quota, len(cellular), min_n=8, max_n=40)
        for name, tax_id, _group in _deprioritize_tax_ids(cellular, {9606, 10090, 10116}):
            jobs.append(
                {
                    "id": f"prot-{_slug(name)}",
                    "kind": "uniprot",
                    "query": _uniprot_reviewed(tax_id),
                    "limit": prot_limit,
                    "category": "protein",
                    "tax_id": tax_id,
                    "reason": "Swiss-Prot proteins",
                }
            )
        jobs.extend(
            [
                {
                    "id": "prot-kw-enzyme",
                    "kind": "uniprot",
                    "query": "(reviewed:true) AND (keyword:KW-0021) AND (length:[150 TO 600])",
                    "limit": min(40, max(12, prot_quota // 20)),
                    "category": "protein",
                    "reason": "enzyme keyword diversity",
                },
                {
                    "id": "prot-kw-membrane",
                    "kind": "uniprot",
                    "query": "(reviewed:true) AND (keyword:KW-0472) AND (length:[150 TO 450])",
                    "limit": min(30, max(10, prot_quota // 24)),
                    "category": "protein",
                    "reason": "membrane proteins",
                },
                {
                    "id": "prot-kw-ribosomal",
                    "kind": "uniprot",
                    "query": "(reviewed:true) AND (keyword:KW-0689) AND (length:[50 TO 250])",
                    "limit": min(30, max(10, prot_quota // 24)),
                    "category": "protein",
                    "reason": "ribosomal proteins",
                },
                {
                    "id": "prot-kw-tf",
                    "kind": "uniprot",
                    "query": "(reviewed:true) AND (keyword:KW-0805) AND (length:[80 TO 400])",
                    "limit": min(24, max(8, prot_quota // 30)),
                    "category": "protein",
                    "reason": "transcription factors",
                },
                {
                    "id": "prot-cas9",
                    "kind": "uniprot",
                    "query": "(reviewed:true) AND (gene:cas9) AND (length:[800 TO 1600])",
                    "limit": min(24, max(8, prot_quota // 40)),
                    "category": "protein",
                    "reason": "reviewed Cas9 proteins, not CRISPR arrays",
                },
                {
                    "id": "prot-cas12",
                    "kind": "uniprot",
                    "query": "(reviewed:true) AND (gene:cas12) AND (length:[400 TO 1600])",
                    "limit": min(16, max(6, prot_quota // 50)),
                    "category": "protein",
                    "reason": "reviewed Cas12 proteins",
                },
                {
                    "id": "prot-cas13",
                    "kind": "uniprot",
                    "query": "(reviewed:true) AND (gene:cas13) AND (length:[400 TO 1400])",
                    "limit": min(12, max(4, prot_quota // 60)),
                    "category": "protein",
                    "reason": "reviewed Cas13 proteins",
                },
            ]
        )

    if allow("pdb", "protein"):
        jobs.append(
            {
                "id": "pdb-structures",
                "kind": "pdb",
                "ids": list(dict.fromkeys(PDB_IDS)),
                "category": "protein",
                "reason": "RCSB polymer entities; duplicates skipped by natural key",
            }
        )

    if allow("ncbi", "virus"):
        vlimit = _limit(virus_quota, len(VIRUS_FAMILIES), min_n=8, max_n=36)
        for family, bucket in VIRUS_FAMILIES:
            jobs.append(
                {
                    "id": f"virus-{_slug(family)}",
                    "kind": "ncbi",
                    "term": _virus_complete(family),
                    "limit": vlimit,
                    "seq_type": "virus",
                    "category": "virus",
                    "reason": f"viral biodiversity ({bucket})",
                }
            )

    if allow("ncbi", "crispr"):
        climit = _limit(crispr_quota, len(prokaryotes), min_n=6, max_n=28)
        for name, tax_id, _group in _deprioritize_tax_ids(prokaryotes, {562}):
            jobs.append(
                {
                    "id": f"crispr-{_slug(name)}",
                    "kind": "ncbi",
                    "term": _crispr_org(name),
                    "limit": climit,
                    "seq_type": "crispr",
                    "category": "crispr",
                    "tax_id": tax_id,
                    "reason": "natural CRISPR locus/array records",
                    "evidence_type": "natural_crispr_element",
                }
            )
        jobs.append(
            {
                "id": "crispr-archaea-fill",
                "kind": "ncbi",
                "term": f'CRISPR[Title] AND Archaea[Organism] AND {_CRISPR_SLEN}',
                "limit": min(40, max(12, crispr_quota // 8)),
                "seq_type": "crispr",
                "category": "crispr",
                "reason": "archaeal CRISPR diversity fill",
                "evidence_type": "natural_crispr_element",
            }
        )

    if allow("genomes", "genome"):
        genome_taxa = [
            "Arabidopsis thaliana",
            "Oryza sativa",
            "Chlamydomonas reinhardtii",
            "Saccharomyces cerevisiae",
            "Streptomyces coelicolor",
            "Methanocaldococcus jannaschii",
            "Haloferax volcanii",
            "Plasmodium falciparum",
            "Danio rerio",
            "Gallus gallus",
            "Anolis carolinensis",
            "Xenopus tropicalis",
            "Drosophila melanogaster",
            "Mammuthus primigenius",
            "Loxodonta africana",
            "Escherichia coli",
            "Mus musculus",
            "Homo sapiens",
        ]
        for name in genome_taxa:
            jobs.append(
                {
                    "id": f"asm-{_slug(name)}",
                    "kind": "genomes",
                    "taxon": name,
                    "limit": 6,
                    "category": "genome",
                    "reason": "assembly metadata only; no chromosome residues",
                }
            )

    if "crispr" in wanted:
        jobs.append(
            {
                "id": "crispr-computational-ngg",
                "kind": "computational_ngg",
                "limit": 120,
                "category": "crispr",
                "reason": "Cas9 NGG scan on allowlisted authentic DNA; labeled COMPUTATIONAL",
            }
        )

    return jobs


def summarize_plan(jobs: list[dict[str, Any]]) -> dict[str, Any]:
    by_category: dict[str, int] = {}
    by_kind: dict[str, int] = {}
    estimated = 0
    for job in jobs:
        cat = str(job.get("category") or "other")
        kind = str(job.get("kind") or "other")
        by_category[cat] = by_category.get(cat, 0) + 1
        by_kind[kind] = by_kind.get(kind, 0) + 1
        if kind == "pdb":
            estimated += len(job.get("ids") or [])
        else:
            estimated += int(job.get("limit") or 0)
    return {
        "jobs": len(jobs),
        "by_category": by_category,
        "by_kind": by_kind,
        "estimated_fetch_ceiling": estimated,
        "taxa_seeded": len(all_cellular_taxa()),
        "virus_families": len(VIRUS_FAMILIES),
        "computational_tax_ids": sorted(COMPUTATIONAL_TAX_IDS),
    }


def build_shortfall_jobs(
    remaining: int,
    *,
    categories: set[str] | None = None,
) -> list[dict[str, Any]]:
    """Extra clade/marker jobs for categories that are still scientifically short.

    Distinct Entrez/UniProt terms — not a second pass over the same first-N hits.
    When ``categories`` is set, DNA/RNA fill is omitted unless those categories
    are explicitly requested.
    """
    extra = max(40, remaining)
    per = min(180, max(40, extra // 12))
    wanted = categories
    jobs: list[dict[str, Any]] = [
        {
            "id": "fill2-dna-actinopterygii",
            "kind": "ncbi",
            "term": f'Actinopterygii[Organism] AND biomol_genomic[PROP] AND "complete cds"[Title] AND {_DNA_SLEN}',
            "limit": per,
            "seq_type": "dna",
            "category": "dna",
            "reason": "teleost CDS shortfall fill",
        },
        {
            "id": "fill2-dna-insecta",
            "kind": "ncbi",
            "term": f'Insecta[Organism] AND biomol_genomic[PROP] AND "complete cds"[Title] AND {_DNA_SLEN}',
            "limit": per,
            "seq_type": "dna",
            "category": "dna",
            "reason": "insect CDS shortfall fill",
        },
        {
            "id": "fill2-dna-streptophyta",
            "kind": "ncbi",
            "term": f'Streptophyta[Organism] AND biomol_genomic[PROP] AND "complete cds"[Title] AND {_DNA_SLEN}',
            "limit": per,
            "seq_type": "dna",
            "category": "dna",
            "reason": "land-plant CDS shortfall fill",
        },
        {
            "id": "fill2-dna-ascomycota",
            "kind": "ncbi",
            "term": f'Ascomycota[Organism] AND biomol_genomic[PROP] AND "complete cds"[Title] AND {_DNA_SLEN}',
            "limit": per,
            "seq_type": "dna",
            "category": "dna",
            "reason": "ascomycete CDS shortfall fill",
        },
        {
            "id": "fill2-dna-actinobacteria",
            "kind": "ncbi",
            "term": f'Actinomycetota[Organism] AND biomol_genomic[PROP] AND "complete cds"[Title] AND {_DNA_SLEN}',
            "limit": per,
            "seq_type": "dna",
            "category": "dna",
            "reason": "actinobacterial CDS shortfall fill",
        },
        {
            "id": "fill2-dna-bacillota",
            "kind": "ncbi",
            "term": f'Bacillota[Organism] AND biomol_genomic[PROP] AND "complete cds"[Title] AND {_DNA_SLEN}',
            "limit": per,
            "seq_type": "dna",
            "category": "dna",
            "reason": "Bacillota CDS shortfall fill",
        },
        {
            "id": "fill2-dna-pseudomonadota",
            "kind": "ncbi",
            "term": f'Pseudomonadota[Organism] AND biomol_genomic[PROP] AND "complete cds"[Title] AND {_DNA_SLEN}',
            "limit": per,
            "seq_type": "dna",
            "category": "dna",
            "reason": "Pseudomonadota CDS shortfall fill",
        },
        {
            "id": "fill2-dna-euryarchaeota",
            "kind": "ncbi",
            "term": f'Euryarchaeota[Organism] AND biomol_genomic[PROP] AND "complete cds"[Title] AND {_DNA_SLEN}',
            "limit": min(80, per),
            "seq_type": "dna",
            "category": "dna",
            "reason": "euryarchaeal CDS shortfall fill",
        },
        {
            "id": "fill2-rna-alveolata",
            "kind": "ncbi",
            "term": f'Alveolata[Organism] AND biomol_mrna[PROP] AND refseq[filter] AND {_RNA_SLEN}',
            "limit": min(80, per),
            "seq_type": "rna",
            "category": "rna",
            "reason": "alveolate mRNA shortfall fill",
        },
        {
            "id": "fill2-rna-basidiomycota",
            "kind": "ncbi",
            "term": f'Basidiomycota[Organism] AND biomol_mrna[PROP] AND refseq[filter] AND {_RNA_SLEN}',
            "limit": min(80, per),
            "seq_type": "rna",
            "category": "rna",
            "reason": "basidiomycete mRNA shortfall fill",
        },
        {
            "id": "fill2-prot-bacteria",
            "kind": "uniprot",
            "query": "(taxonomy_id:2) AND (reviewed:true) AND (length:[80 TO 500])",
            "limit": min(200, max(50, extra // 8)),
            "category": "protein",
            "reason": "Swiss-Prot bacteria clade fill",
        },
        {
            "id": "fill2-prot-archaea",
            "kind": "uniprot",
            "query": "(taxonomy_id:2157) AND (reviewed:true) AND (length:[80 TO 500])",
            "limit": min(120, max(30, extra // 12)),
            "category": "protein",
            "reason": "Swiss-Prot archaea clade fill",
        },
        {
            "id": "fill2-prot-viridiplantae",
            "kind": "uniprot",
            "query": "(taxonomy_id:33090) AND (reviewed:true) AND (length:[80 TO 500])",
            "limit": min(120, max(30, extra // 12)),
            "category": "protein",
            "reason": "Swiss-Prot plant clade fill",
        },
        {
            "id": "fill2-prot-fungi",
            "kind": "uniprot",
            "query": "(taxonomy_id:4751) AND (reviewed:true) AND (length:[80 TO 500])",
            "limit": min(120, max(30, extra // 12)),
            "category": "protein",
            "reason": "Swiss-Prot fungal clade fill",
        },
        {
            "id": "fill2-prot-animals",
            "kind": "uniprot",
            "query": "(taxonomy_id:33208) AND (reviewed:true) AND (length:[80 TO 500])",
            "limit": min(120, max(30, extra // 12)),
            "category": "protein",
            "reason": "Swiss-Prot metazoan clade fill",
        },
        {
            "id": "fill2-prot-refseq-archaea",
            "kind": "ncbi",
            "term": "Archaea[Organism] AND srcdb_refseq[PROP] AND 80:600[SLEN]",
            "limit": min(80, per),
            "seq_type": "protein",
            "db": "protein",
            "category": "protein",
            "reason": "RefSeq archaeal proteins (distinct provenance from UniProt)",
        },
        {
            "id": "fill2-virus-genbank",
            "kind": "ncbi",
            "term": f'Viruses[Organism] AND "complete genome"[Title] AND srcdb_genbank[PROP] AND {_VIRUS_SLEN}',
            "limit": min(120, per),
            "seq_type": "virus",
            "category": "virus",
            "reason": "GenBank complete viral genomes beyond RefSeq-only family jobs",
        },
        {
            "id": "fill2-crispr-bacteria-not-ecoli",
            "kind": "ncbi",
            "term": f'CRISPR[Title] AND Bacteria[Organism] NOT "Escherichia coli"[Organism] AND {_CRISPR_SLEN}',
            "limit": min(120, per),
            "seq_type": "crispr",
            "category": "crispr",
            "reason": "natural CRISPR loci outside E. coli",
            "evidence_type": "natural_crispr_element",
        },
        {
            "id": "fill2-crispr-archaea",
            "kind": "ncbi",
            "term": f'CRISPR[Title] AND Archaea[Organism] AND {_CRISPR_SLEN}',
            "limit": min(80, per),
            "seq_type": "crispr",
            "category": "crispr",
            "reason": "additional archaeal CRISPR loci",
            "evidence_type": "natural_crispr_element",
        },
        {
            "id": "fill2-crispr-computational-ngg",
            "kind": "computational_ngg",
            "limit": 80,
            "category": "crispr",
            "reason": "second Cas9 NGG pass after newly ingested allowlisted DNA",
        },
    ]
    if wanted is None:
        return jobs
    return [job for job in jobs if str(job.get("category") or "") in wanted]
