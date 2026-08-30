"""Deterministic, source-backed Paleogenomics narratives.

Last reviewed: 2026-08-30. No runtime generative model.
PMIDs are NCBI-verified (see citations.py).
"""

from __future__ import annotations

from datetime import date

from app.pipeline.paleogenomics import citations as C

REVIEWED = date(2026, 8, 30)

# section_key, title, evidence_level, body, pmids, dois [, urls]
Claim = tuple[str, str, str, str, tuple[int, ...], tuple[str, ...]]
ClaimRow = tuple


def _claims(*rows: ClaimRow) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for order, row in enumerate(rows):
        key, title, evidence, body, pmids, dois = row[:6]
        urls = row[6] if len(row) > 6 else ()
        out.append(
            {
                "section_key": key,
                "title": title,
                "evidence_level": evidence,
                "body": body.strip(),
                "pubmed_ids": list(pmids),
                "dois": list(dois),
                "urls": list(urls),
                "sort_order": order,
                "last_reviewed_on": REVIEWED.isoformat(),
            }
        )
    return out


NARRATIVES: dict[str, list[dict[str, object]]] = {
    "homo-neanderthalensis": _claims(
        (
            "overview",
            "Overview",
            "consensus",
            """
NCBI currently lists this taxon as Homo sapiens neanderthalensis (TaxID 63221),
a subspecies of Homo sapiens. Many papers use Homo neanderthalensis. BioWiki
keeps the NCBI TaxID and does not merge palaeogenomic records with living
Homo sapiens (9606). These are ancient specimen genomes. Introgressed segments
in living people are catalogued separately.
""",
            (C.GREEN_2010_NEANDERTHAL_DRAFT, C.PRUFER_2014_ALTAI_NEANDERTHAL),
            (),
        ),
        (
            "evolution",
            "Evolution",
            "strong_evidence",
            """
Neanderthals diverged from the lineage leading to present-day Homo sapiens in
the Middle Pleistocene. Genomic divergence dates depend on mutation-rate and
generation-time assumptions and are reported as ranges. They are more closely
related to Denisovans than to most present-day Africans, consistent with a
shared archaic Eurasian branch after the split from the modern-human lineage.
""",
            (C.PRUFER_2014_ALTAI_NEANDERTHAL, C.KRAUSE_2010_DENISOVA),
            (),
        ),
        (
            "range",
            "Time and geographic range",
            "strong_evidence",
            """
The fossil and genomic record places Neanderthals across Eurasia in the Middle
and Late Pleistocene. Last unambiguous fossils date to roughly 40 thousand
years ago. Precise last-occurrence years remain site-dependent.
""",
            (C.GREEN_2010_NEANDERTHAL_DRAFT,),
            (),
        ),
        (
            "ecology",
            "Life and ecology",
            "supported_hypothesis",
            """
Fossil, isotopic and archaeological evidence indicate use of stone technology
and diets that often included large herbivores, with regional variation
including plant foods. Behavioural interpretations (language, symbolic culture)
remain actively researched. Popular stereotypes of intelligence are not
scientific facts.
""",
            (C.GREEN_2010_NEANDERTHAL_DRAFT,),
            (),
        ),
        (
            "extinction",
            "Disappearance",
            "debated",
            """
Neanderthals disappear from the fossil record in the Late Pleistocene. Proposed
contributors include climate variability, small population size, competition or
admixture with expanding Homo sapiens, and demographic stochasticity. No single
cause is established as sufficient on its own.
""",
            (C.PRUFER_2017_VINDIJA,),
            (),
        ),
        (
            "paleogenomics",
            "Paleogenomics",
            "consensus",
            """
High-coverage nuclear genomes exist from individuals including the Altai
(Denisova Cave) Neanderthal, Vindija, and Chagyrskaya, plus mitochondrial
datasets. These are ancient specimen genomes. Modern-human Neanderthal ancestry
is a different evidence class.
""",
            (
                C.PRUFER_2014_ALTAI_NEANDERTHAL,
                C.PRUFER_2017_VINDIJA,
                C.MAFESSONI_2020_CHAGYRSKAYA,
                C.GREEN_2008_NEANDERTHAL_MT,
            ),
            (),
        ),
        (
            "significance",
            "Scientific importance",
            "consensus",
            """
Neanderthal genomes underpin research on hominin phylogeny, mutation rates,
and the history of contact with Homo sapiens.
""",
            (C.GREEN_2010_NEANDERTHAL_DRAFT, C.SANKARARAMAN_2014_NEANDERTHAL_ANCESTRY),
            (),
        ),
        (
            "modern",
            "Why it matters now",
            "consensus",
            """
Archaic ancestry in living people is a population-genetic estimate. It varies
among individuals and datasets. It is not an ethnic classification and is not
“exactly 2% in all non-Africans.” Main Neanderthal–modern-human admixture is
generally placed tens of thousands of years ago, commonly around ~50–60 ka
depending on study and model. The ~550–765 ka scale concerns deeper lineage
divergence, not that main introgression pulse. Phenotype associations reported
for archaic haplotypes (for example Simonti et al. 2016) are statistical and
must not be read as medical diagnosis or a deterministic trait.
""",
            (
                C.SANKARARAMAN_2014_NEANDERTHAL_ANCESTRY,
                C.VERNOT_2016_COMBINED_ARCHAIC,
                C.SIMONTI_2016_PHENOTYPIC_LEGACY,
            ),
            (),
        ),
        (
            "uncertainty",
            "Uncertainties / debates",
            "debated",
            """
Last-occurrence chronology is site-dependent. Behavioural reconstructions
(language, symbolism) remain active research. Introgression maps differ by
reference panel, method and cohort. Direct specimen genomes (TaxID 63221) must
not be conflated with living-human ancestry segments (TaxID 9606).
""",
            (C.PRUFER_2017_VINDIJA, C.SANKARARAMAN_2014_NEANDERTHAL_ANCESTRY),
            (),
        ),
        (
            "deextinction",
            "De-extinction / restoration",
            "consensus",
            """
There is no scientifically accepted programme that has resurrected Neanderthals.
Ethical, legal and biological barriers are extreme. BioWiki does not treat
science-fiction scenarios as research status.
""",
            (),
            (),
        ),
    ),
    "homo-denisova": _claims(
        (
            "overview",
            "Overview",
            "strong_evidence",
            """
Denisovans are known primarily from genomic sequences first reported from
Denisova Cave, Siberia. NCBI lists the taxon as Homo sapiens subsp. 'Denisova'
(TaxID 741158). Species-level Linnaean naming remains unsettled; BioWiki keeps
the NCBI label and does not invent a Homo species epithet.
""",
            (C.KRAUSE_2010_DENISOVA, C.MEYER_2012_DENISOVAN),
            (),
        ),
        (
            "evolution",
            "Evolution",
            "strong_evidence",
            """
Denisovans form a sister group to Neanderthals among sequenced archaic
Eurasians. Relationships to fragmentary Asian fossils are often uncertain.
Proposed identification of the Harbin cranium (Homo longi) with this lineage
is a scientific debate, not NCBI taxonomy.
""",
            (C.MEYER_2012_DENISOVAN, C.KRAUSE_2010_DENISOVA),
            (),
        ),
        (
            "range",
            "Time and geographic range",
            "supported_hypothesis",
            """
Occupancy of the Altai is genetically documented. Related ancestry in ancient
and modern populations of Asia and Oceania is genetically inferred. A complete
geographic range from fossils alone is not established.
""",
            (C.MEYER_2012_DENISOVAN,),
            (),
        ),
        (
            "ecology",
            "Life and ecology",
            "unknown",
            """
Direct ecological reconstruction is limited by the sparse fossil sample.
Behaviour and diet are not reconstructed here beyond what fossils and sites
actually support.
""",
            (C.MEYER_2012_DENISOVAN,),
            (),
        ),
        (
            "extinction",
            "Disappearance",
            "unknown",
            """
The timing and process of Denisovan disappearance are not established with the
same fossil density as for Neanderthals. Genomic traces persist as ancestry in
some present-day populations.
""",
            (C.MEYER_2012_DENISOVAN,),
            (),
        ),
        (
            "paleogenomics",
            "Paleogenomics",
            "consensus",
            """
A high-coverage Denisovan genome and additional specimens provide authentic
nuclear and mitochondrial DNA. These are ancient specimen records, not modern
Oceanian genomes with Denisovan ancestry.
""",
            (C.MEYER_2012_DENISOVAN,),
            (),
        ),
        (
            "significance",
            "Scientific importance",
            "consensus",
            """
Denisovan genomes revealed a previously unknown archaic population and a source
of ancestry in living humans, including the EPAS1 high-altitude haplotype in
Tibetans.
""",
            (C.HUERTA_SANCHEZ_2014_EPAS1,),
            (),
        ),
        (
            "modern",
            "Why it matters now",
            "consensus",
            """
Denisovan ancestry is a genetic inference about living Homo sapiens. It must not
be displayed as DNA extracted from a Denisovan bone.
""",
            (C.HUERTA_SANCHEZ_2014_EPAS1, C.VERNOT_2016_COMBINED_ARCHAIC),
            (),
        ),
        (
            "deextinction",
            "De-extinction / restoration",
            "consensus",
            """
No authentic de-extinction programme applies to Denisovans.
""",
            (),
            (),
        ),
    ),
    "raphus-cucullatus": _claims(
        (
            "overview",
            "Overview",
            "consensus",
            """
The dodo (Raphus cucullatus) was a large, flightless columbid endemic to
Mauritius. It is not a Malagasy endemic and did not evolve because Madagascar
rifted from Africa. Mitochondrial DNA places it among Indo-Pacific pigeons,
closest to the Nicobar pigeon among living species in Shapiro et al. 2002.
""",
            (C.SHAPIRO_2002_FLIGHT_OF_THE_DODO,),
            (),
        ),
        (
            "evolution",
            "How the lineage evolved",
            "strong_evidence",
            """
Island colonization of the Mascarenes by a volant pigeon ancestor, followed by
loss of flight, is the supported evolutionary pathway. Divergence dates are
model-dependent. Evolution had no goal; flightlessness is a repeated island
outcome, not evidence of inferiority.
""",
            (C.SHAPIRO_2002_FLIGHT_OF_THE_DODO,),
            (),
        ),
        (
            "range",
            "Time and geographic range",
            "consensus",
            """
The species is known only from Mauritius. Subfossil material and historical
accounts do not support a Madagascar origin.
""",
            (C.SHAPIRO_2002_FLIGHT_OF_THE_DODO, C.ANGELES_2017_DODO_HISTOLOGY),
            (),
        ),
        (
            "ecology",
            "Life and ecology",
            "supported_hypothesis",
            """
Bone histology has been used to infer seasonal growth and molt timing. Many
popular claims (extreme stupidity, inability to nest) are later caricatures
rather than field data. Ecological roles such as seed interactions are
plausible but not all are directly measured.
""",
            (C.ANGELES_2017_DODO_HISTOLOGY,),
            (),
        ),
        (
            "extinction",
            "Extinction",
            "strong_evidence",
            """
Human arrival on Mauritius, hunting, habitat transformation, and introduced
mammals that likely depredated eggs and chicks are the principal documented
pressures. Last-occurrence dates are uncertain within the late 17th century
(often cited between 1662 and 1693). A single-cause story is not required by
the evidence.
""",
            (C.ANGELES_2017_DODO_HISTOLOGY,),
            (C.CHEKE_2006_IBIS_DOI, C.HUME_2006_HIST_BIOL_DOI),
        ),
        (
            "paleogenomics",
            "Paleogenomics",
            "strong_evidence",
            """
Museum specimens have yielded mitochondrial sequences used to place the dodo
in the columbid tree. Public GenBank/RefSeq nuccore for TaxID 187135 comprises
four validated records: complete mitogenomes KX902236 and RefSeq NC_031864
(the same mitochondrial genome in two INSDC representations) plus partial
cytb AF483338 and 12S AF483301. That is source-limited public curation, not a
catalogue failure. A BioProject may exist without a chromosome-scale NCBI
Assembly. Absence of further Sequence rows does not mean no museum specimen
exists.
""",
            (C.SHAPIRO_2002_FLIGHT_OF_THE_DODO,),
            (),
        ),
        (
            "significance",
            "Scientific importance",
            "consensus",
            """
The dodo is a type case of historic island extinction and of using museum
genomics to place an extinct bird in the columbid tree.
""",
            (C.SHAPIRO_2002_FLIGHT_OF_THE_DODO,),
            (),
        ),
        (
            "modern",
            "Why it matters now",
            "consensus",
            """
It informs island conservation (introduced predators, rapid human impact) and
museum DNA methods. Company de-extinction language about “bringing back the
dodo” describes trait engineering in living pigeons if pursued, not a
demonstration that Raphus cucullatus has been recreated. Nature Biotechnology
(2025) notes that resulting organisms would not be exact copies of the
historical species. A May 2026 Nature news article on synthetic-egg technology
explicitly urged caution about what company-reported avian incubation
demonstrates.
""",
            (C.NATURE_BIOTECH_2025_COLOSSAL_DODO, C.NATURE_2026_SYNTHETIC_EGG),
            (),
        ),
        (
            "deextinction",
            "De-extinction / restoration",
            "supported_hypothesis",
            """
Colossal Biosciences has publicly described a dodo project using the Nicobar
pigeon as a genomic model. Nature Biotechnology 2025 reported that fundraising
and programme language covering mammoth, thylacine and dodo, and stated that
resulting organisms would not be exact copies of the historical species. A
May 2026 Nature news article discussed synthetic-egg technology in the context
of extinct birds including dodo/moa and urged caution. That is journal news
and organization-reported progress toward a proxy, not peer-reviewed evidence
that Raphus cucullatus has been resurrected. A modified living relative is not
automatically the original taxon.
""",
            (
                C.SHAPIRO_2002_FLIGHT_OF_THE_DODO,
                C.NATURE_BIOTECH_2025_COLOSSAL_DODO,
                C.NATURE_2026_SYNTHETIC_EGG,
            ),
            (C.NATURE_BIOTECH_2025_DOI, C.NATURE_2026_SYNTHETIC_EGG_DOI),
        ),
        (
            "uncertainty",
            "Uncertainties / debates",
            "debated",
            """
Last-occurrence year within the late 17th century remains uncertain. Relative
contributions of hunting, habitat change and introduced mammals cannot be
partitioned with experimental precision from the historical record. Popular
caricatures of intelligence are not data.
""",
            (C.ANGELES_2017_DODO_HISTOLOGY,),
            (C.CHEKE_2006_IBIS_DOI, C.HUME_2006_HIST_BIOL_DOI),
        ),
    ),
}


NARRATIVES["thylacinus-cynocephalus"] = _claims(
    (
        "overview",
        "Overview",
        "consensus",
        """
Thylacinus cynocephalus, the thylacine, was the largest recent carnivorous
marsupial. It survived into the 20th century in Tasmania after earlier mainland
loss. The last captive animal died in 1936.
""",
        (C.MILLER_2009_THYLACINE_MT, C.FEIGIN_2018_THYLACINE_GENOME),
        (),
    ),
    (
        "evolution",
        "Evolution",
        "strong_evidence",
        """
Thylacines belong to Thylacinidae within Dasyuromorphia, not to placental
canids. Superficial dog-like anatomy is convergent. A nuclear genome from a
museum pouch specimen clarifies relationships among Australian marsupial carnivores.
""",
        (C.FEIGIN_2018_THYLACINE_GENOME,),
        (),
    ),
    (
        "range",
        "Time and geographic range",
        "consensus",
        """
The species occupied mainland Australia and Tasmania in the Holocene. Mainland
disappearance preceded the historically documented Tasmanian population.
""",
        (C.FEIGIN_2018_THYLACINE_GENOME,),
        (),
    ),
    (
        "ecology",
        "Life and ecology",
        "supported_hypothesis",
        """
It was a faunivore; exact hunting style and pack behaviour are incompletely
documented. Mainland disappearance has been linked to dingoes, climate, and
human hunting in hypotheses of varying strength.
""",
        (C.FEIGIN_2018_THYLACINE_GENOME,),
        (),
    ),
    (
        "extinction",
        "Extinction",
        "strong_evidence",
        """
Legislated bounties and persecution in Tasmania are historically documented.
Whether disease or ecological change were necessary cofactors remains discussed.
Unverified post-1936 sightings are not treated here as occurrence records.
""",
        (C.FEIGIN_2018_THYLACINE_GENOME,),
        (),
    ),
    (
        "paleogenomics",
        "Paleogenomics",
        "consensus",
        """
A mitochondrial genome from a museum specimen and a nuclear genome assembly
from a juvenile pouch specimen have been published. These are authentic museum
genomics, not SRA-read catalogues.
""",
        (C.MILLER_2009_THYLACINE_MT, C.FEIGIN_2018_THYLACINE_GENOME),
        (),
    ),
    (
        "significance",
        "Scientific importance",
        "consensus",
        """
The thylacine genome is a resource for marsupial evolution, extinction biology,
and the genetics of a recently lost predator.
""",
        (C.FEIGIN_2018_THYLACINE_GENOME,),
        (),
    ),
    (
        "modern",
        "Why it matters now",
        "consensus",
        """
It is a reference for conservation genomics of Tasmanian fauna and for
evaluating de-extinction claims.
""",
        (C.FEIGIN_2018_THYLACINE_GENOME,),
        (),
    ),
    (
        "deextinction",
        "De-extinction / restoration",
        "supported_hypothesis",
        """
Colossal Biosciences and academic collaborators have described thylacine genome
engineering using dasyurid models. Published genomes (Miller 2009; Feigin 2018)
are peer-reviewed. Nature Biotechnology 2025 reported company fundraising and
programme language covering mammoth, thylacine and dodo, and stated that
resulting organisms would not be exact copies of the historical species.
Resurrection of Thylacinus cynocephalus has not been demonstrated. Proxy
neonates would not automatically be the historical species.
""",
        (
            C.FEIGIN_2018_THYLACINE_GENOME,
            C.NATURE_BIOTECH_2025_COLOSSAL_DODO,
        ),
        (C.NATURE_BIOTECH_2025_DOI,),
    ),
    (
        "uncertainty",
        "Uncertainties / debates",
        "debated",
        """
Disease and ecological change as cofactors in Tasmanian extinction remain
discussed. Post-1936 sightings are not occurrence records here. De-extinction
timelines and trait lists from companies are organization-reported, not
independent proof of a living thylacine.
""",
        (C.FEIGIN_2018_THYLACINE_GENOME,),
        (),
    ),
)

NARRATIVES["coelodonta-antiquitatis"] = _claims(
    (
        "overview",
        "Overview",
        "consensus",
        """
Coelodonta antiquitatis, the woolly rhinoceros, was a cold-adapted rhinocerotid
of Pleistocene northern Eurasia, part of the mammoth-steppe fauna.
""",
        (C.LORD_2020_WOOLLY_RHINO,),
        (),
    ),
    (
        "evolution",
        "Evolution",
        "strong_evidence",
        """
Ancient genomes place woolly rhinoceroses on the rhinocerotid tree with
adaptations inferred for cold environments. They are an extinct species with
their own history, not frozen modern rhinos.
""",
        (C.LORD_2020_WOOLLY_RHINO,),
        (),
    ),
    (
        "range",
        "Time and geographic range",
        "strong_evidence",
        """
The species occupied cold Pleistocene habitats across northern Eurasia.
Last occurrences fall near 14 thousand years ago in the sampled record.
""",
        (C.LORD_2020_WOOLLY_RHINO,),
        (),
    ),
    (
        "ecology",
        "Life and ecology",
        "strong_evidence",
        """
Morphology and palaeoenvironmental data indicate grazing on open steppe-tundra
vegetation.
""",
        (C.LORD_2020_WOOLLY_RHINO,),
        (),
    ),
    (
        "extinction",
        "Extinction",
        "debated",
        """
Lord et al. 2020 reported genomic evidence of relatively stable demography until
close to extinction and argued that rapid warming during the Bølling–Allerød
is a major hypothesis, while human hunting may have contributed regionally.
Guðjónsdóttir et al. 2026 analysed a high-coverage genome from tissue about
14,400 years old recovered from the stomach contents of an ancient wolf
(Tumat, northeastern Siberia) and compared it with other Late Pleistocene
woolly-rhinoceros genomes. They reported no evidence of major recent inbreeding
or genomic erosion in that near-extinction specimen, which they interpret as
supporting a relatively rapid final collapse rather than long-term inbreeding
depression immediately before extinction. Those results apply to the sampled
lineage and time slice. BioWiki does not assign a single universal cause:
climate, metapopulation structure and regional human presence remain part of
the published discussion.
""",
        (C.LORD_2020_WOOLLY_RHINO, C.GUDJONSDOTTIR_2026_WOOLLY_RHINO_INBREEDING),
        (C.GUDJONSDOTTIR_2026_GBE_DOI,),
        (),
    ),
    (
        "paleogenomics",
        "Paleogenomics",
        "consensus",
        """
A complete nuclear genome and multiple mitogenomes have been reported, including
the 2026 high-coverage Tumat specimen preserved in ancient wolf stomach
contents. Nuclear assemblies, when public, belong in genome_records rather than
as gigabase Sequence rows. Public nuccore for TaxID 222863 is source-limited
relative to the preferred discovery goal; that is not a reason to invent
accessions.
""",
        (C.LORD_2020_WOOLLY_RHINO, C.GUDJONSDOTTIR_2026_WOOLLY_RHINO_INBREEDING),
        (C.GUDJONSDOTTIR_2026_GBE_DOI,),
        (),
    ),
    (
        "significance",
        "Scientific importance",
        "consensus",
        """
Woolly rhinoceros genomics tests how megafauna responded to glacial cycles
independently of the mammoth.
""",
        (C.LORD_2020_WOOLLY_RHINO,),
        (),
    ),
    (
        "modern",
        "Why it matters now",
        "consensus",
        """
It is a comparator for climate-driven range collapse and for rhinoceros
conservation genomics.
""",
        (C.LORD_2020_WOOLLY_RHINO,),
        (),
    ),
    (
        "deextinction",
        "De-extinction / restoration",
        "consensus",
        """
No high-profile commercial de-extinction programme currently targets this
species with the visibility of mammoth, dodo or thylacine. Status: no active
programme documented here. Genomic work on extinction process is not a
restoration programme.
""",
        (C.GUDJONSDOTTIR_2026_WOOLLY_RHINO_INBREEDING,),
        (C.GUDJONSDOTTIR_2026_GBE_DOI,),
    ),
    (
        "uncertainty",
        "Uncertainties / debates",
        "debated",
        """
Whether climate warming, humans, or both drove the final loss likely varied by
region. The 2026 Tumat genome argues against recent inbreeding as a necessary
prelude in that specimen; it does not by itself prove a single-cause extinction
across the species’ range.
""",
        (C.LORD_2020_WOOLLY_RHINO, C.GUDJONSDOTTIR_2026_WOOLLY_RHINO_INBREEDING),
        (),
    ),
)

NARRATIVES["mammuthus-primigenius"] = _claims(
    (
        "overview",
        "Overview",
        "consensus",
        """
Mammuthus primigenius, the woolly mammoth, inhabited Pleistocene mammoth-steppe
across northern Eurasia and North America. Molecular phylogenies place mammoths
closer to Asian elephants than to African forest and savanna elephants.
""",
        (C.ROHLAND_2010_ELEPHANTID_SPECIATION, C.PALKOPOULOU_2015_MAMMOTH_GENOMES),
        (),
    ),
    (
        "evolution",
        "Evolution",
        "strong_evidence",
        """
Mammoths diversified in the Pliocene–Pleistocene elephantid radiation. Million-year-old
molar DNA from Siberia has been used to reconstruct earlier mammoth lineages.
Island populations (including Wrangel) persisted into the Holocene.
""",
        (C.VAN_DER_VALK_2021_MILLION_YEAR_MAMMOTH, C.PALKOPOULOU_2015_MAMMOTH_GENOMES),
        (),
    ),
    (
        "range",
        "Time and geographic range",
        "strong_evidence",
        """
The species was Holarctic in the Late Pleistocene. Mainland extinction around
the Pleistocene–Holocene transition was not globally synchronous with Wrangel
Island survival until about 4 ka.
""",
        (C.PALKOPOULOU_2015_MAMMOTH_GENOMES,),
        (),
    ),
    (
        "ecology",
        "Life and ecology",
        "strong_evidence",
        """
They were bulk grazers/browsers of open steppe-tundra and likely affected
vegetation structure. Ecosystem engineering is inferred, not filmed.
""",
        (C.PALKOPOULOU_2015_MAMMOTH_GENOMES,),
        (),
    ),
    (
        "extinction",
        "Extinction",
        "debated",
        """
Complete genomes show signatures of demographic and genetic decline. Climate
and vegetation change and human presence coincide regionally. Neither “humans
killed every mammoth” nor “climate alone” is an adequate one-line summary.
""",
        (C.PALKOPOULOU_2015_MAMMOTH_GENOMES,),
        (),
    ),
    (
        "paleogenomics",
        "Paleogenomics",
        "consensus",
        """
Nuclear genomes from permafrost specimens, including high-coverage individuals
and million-year-old molar DNA, are published. Chromosome-scale assemblies must
be stored as GenomeRecord metadata in BioWiki.
""",
        (C.PALKOPOULOU_2015_MAMMOTH_GENOMES, C.VAN_DER_VALK_2021_MILLION_YEAR_MAMMOTH),
        (),
    ),
    (
        "significance",
        "Scientific importance",
        "consensus",
        """
Mammoth palaeogenomics is a flagship system for ancient DNA, demography, and
cold adaptation.
""",
        (C.PALKOPOULOU_2015_MAMMOTH_GENOMES,),
        (),
    ),
    (
        "modern",
        "Why it matters now",
        "consensus",
        """
It informs climate-driven extinction, elephant conservation genetics, and
evaluating de-extinction engineering that uses Asian elephant cells as a
chassis.
""",
        (C.VAN_DER_VALK_2021_MILLION_YEAR_MAMMOTH,),
        (),
    ),
    (
        "deextinction",
        "De-extinction / restoration",
        "supported_hypothesis",
        """
Colossal Biosciences reports multiplex editing of Asian elephants toward
mammoth-like traits. That is organization-reported genome-engineering research.
Nature Biotechnology 2025 stated that resulting organisms would not be exact
copies of the historical species. A cold-adapted elephant proxy would not
automatically be Mammuthus primigenius under current taxonomy.
""",
        (C.NATURE_BIOTECH_2025_COLOSSAL_DODO,),
        (C.NATURE_BIOTECH_2025_DOI,),
    ),
    (
        "uncertainty",
        "Uncertainties / debates",
        "debated",
        """
Relative roles of climate, humans and ecological feedbacks differ by population
and millennium. Wrangel Island survival into the Holocene shows extinction was
not globally synchronous. Company birth-date roadmaps are not peer-reviewed
timelines.
""",
        (C.PALKOPOULOU_2015_MAMMOTH_GENOMES,),
        (),
    ),
)

NARRATIVES["mammut-americanum"] = _claims(
    (
        "overview",
        "Overview",
        "consensus",
        "Mammut americanum (American mastodon) is a Pleistocene mammutid of the Americas, distinct from mammoths (Mammuthus).",
        (C.ROHLAND_2010_ELEPHANTID_SPECIATION,),
        (),
    ),
    (
        "evolution",
        "Evolution",
        "strong_evidence",
        "Nuclear DNA from mastodon and woolly mammoth shows a deep split between forest and savanna African elephants and places mastodons outside the elephantid crown that includes mammoths.",
        (C.ROHLAND_2010_ELEPHANTID_SPECIATION,),
        (),
    ),
    (
        "range",
        "Time and geographic range",
        "strong_evidence",
        "Mastodons occupied forested and mosaic habitats in North America during the Pleistocene.",
        (C.ROHLAND_2010_ELEPHANTID_SPECIATION,),
        (),
    ),
    (
        "ecology",
        "Life and ecology",
        "strong_evidence",
        "Dental morphology indicates mixed feeding including woody browse, unlike typical mammoth-steppe grazers.",
        (C.ROHLAND_2010_ELEPHANTID_SPECIATION,),
        (),
    ),
    (
        "extinction",
        "Extinction",
        "debated",
        "North American mastodons disappear near the end-Pleistocene. Climate, habitat, and human hunting are all discussed; weighting is regional and unresolved.",
        (C.ROHLAND_2010_ELEPHANTID_SPECIATION,),
        (),
    ),
    (
        "paleogenomics",
        "Paleogenomics",
        "strong_evidence",
        "Mitochondrial and nuclear data exist from subfossil bone. Coverage is generally lower than for woolly mammoth permafrost genomes.",
        (C.ROHLAND_2010_ELEPHANTID_SPECIATION,),
        (),
    ),
    ("significance", "Scientific importance", "consensus", "Mastodon genomes test forest-megafauna responses at the Pleistocene–Holocene boundary.", (C.ROHLAND_2010_ELEPHANTID_SPECIATION,), ()),
    ("modern", "Why it matters now", "consensus", "They illustrate that ‘ice-age elephant’ is not one species and that habitat type matters for extinction models.", (), ()),
    ("deextinction", "De-extinction / restoration", "consensus", "No major public de-extinction programme targets mastodons as of this review date.", (), ()),
)

NARRATIVES["smilodon-populator"] = _claims(
    (
        "overview",
        "Overview",
        "consensus",
        "Smilodon populator is a Pleistocene saber-toothed felid of South America. NCBI TaxID 339609. Popular ‘Smilodon’ often mixes S. fatalis and S. populator.",
        (C.WESTBURY_2021_SMILODON,),
        (),
    ),
    (
        "evolution",
        "Evolution",
        "strong_evidence",
        "A draft nuclear genome from a Chilean specimen dated to 13,182 ± 90 cal BP places Smilodon among machairodontine felids, with a deep split from living cats and no detected gene flow with contemporary Felidae in that study.",
        (C.WESTBURY_2021_SMILODON,),
        (),
    ),
    (
        "range",
        "Time and geographic range",
        "strong_evidence",
        "S. populator is a South American species of the Late Pleistocene. The sequenced specimen is from Ultima Esperanza, Chile.",
        (C.WESTBURY_2021_SMILODON,),
        (),
    ),
    (
        "ecology",
        "Life and ecology",
        "supported_hypothesis",
        "Morphology indicates an ambush predator of large vertebrates. Pack hunting is not established from the genomic paper.",
        (C.WESTBURY_2021_SMILODON,),
        (),
    ),
    (
        "extinction",
        "Extinction",
        "debated",
        "South American megafaunal losses near the end-Pleistocene involve climate and humans; species-specific last dates remain sparse.",
        (C.WESTBURY_2021_SMILODON,),
        (),
    ),
    (
        "paleogenomics",
        "Paleogenomics",
        "strong_evidence",
        "The Westbury et al. draft genome is authentic palaeogenomics. Raw reads are in BioProject PRJNA691254. BioWiki does not import those reads as Sequence rows.",
        (C.WESTBURY_2021_SMILODON,),
        (),
    ),
    ("significance", "Scientific importance", "consensus", "Sabertooth genomics addresses felid phylogeny and Pleistocene predator diversity in the Americas.", (C.WESTBURY_2021_SMILODON,), ()),
    ("modern", "Why it matters now", "consensus", "It is a caution against treating all Pleistocene cats as one ecological unit.", (), ()),
    ("deextinction", "De-extinction / restoration", "consensus", "No credible resurrection programme is documented for S. populator.", (), ()),
)

NARRATIVES["bos-primigenius"] = _claims(
    (
        "overview",
        "Overview",
        "consensus",
        "Bos primigenius, the aurochs, is the wild ancestor of domestic cattle (NCBI TaxID 9909). It is not identical to Bos taurus. The last recorded individual died in 1627 in Poland.",
        (C.PARK_2015_AUROCHS,),
        (),
    ),
    (
        "evolution",
        "Evolution",
        "strong_evidence",
        "A British aurochs genome illuminates cattle phylogeography. Living cattle carry aurochs ancestry but are domesticated lineages.",
        (C.PARK_2015_AUROCHS,),
        (),
    ),
    (
        "range",
        "Time and geographic range",
        "strong_evidence",
        "Aurochsen occupied Eurasian woodlands and open habitats. The historic last record is European; earlier populations were wider.",
        (C.PARK_2015_AUROCHS,),
        (),
    ),
    (
        "ecology",
        "Life and ecology",
        "supported_hypothesis",
        "They were large grazers/browsers. Fine-scale diet varied.",
        (C.PARK_2015_AUROCHS,),
        (),
    ),
    (
        "extinction",
        "Extinction",
        "strong_evidence",
        "Hunting and habitat conversion in historic Europe are documented. The 1627 date is a historical last-occurrence, not a radiocarbon range for all populations.",
        (C.PARK_2015_AUROCHS,),
        (),
    ),
    (
        "paleogenomics",
        "Paleogenomics",
        "consensus",
        "Published aurochs genomes must not be merged taxonomically into Holstein or other B. taurus accessions.",
        (C.PARK_2015_AUROCHS,),
        (),
    ),
    ("significance", "Scientific importance", "consensus", "Aurochs DNA is central to the history of domestication.", (C.PARK_2015_AUROCHS,), ()),
    ("modern", "Why it matters now", "consensus", "Back-breeding programmes produce cattle with aurochs-like traits, not verified B. primigenius.", (), ()),
    ("deextinction", "De-extinction / restoration", "supported_hypothesis", "Breeding programmes aim at ecological proxies. That is not genomic resurrection of the 1627 taxon.", (), ()),
)

NARRATIVES["equus-quagga-quagga"] = _claims(
    (
        "overview",
        "Overview",
        "consensus",
        "The quagga is Equus quagga quagga (NCBI TaxID 555873), a subspecies of the plains zebra, not a separate zebra species. The last captive animal died in 1883.",
        (C.HIGUCHI_1984_QUAGGA,),
        (),
    ),
    (
        "evolution",
        "Evolution",
        "strong_evidence",
        "Higuchi et al. 1984 recovered DNA sequences from a quagga museum specimen — among the first extinct-animal DNA reports. Later taxonomy nests the quagga within plains zebra diversity.",
        (C.HIGUCHI_1984_QUAGGA,),
        (),
    ),
    (
        "range",
        "Time and geographic range",
        "supported_hypothesis",
        "Historical range was arid grassland in southern Africa. Ecology is inferred from historical range and zebra biology.",
        (),
        (),
    ),
    (
        "ecology",
        "Life and ecology",
        "supported_hypothesis",
        "It occupied southern African grasslands. Detailed foraging studies of the extinct subspecies are limited.",
        (),
        (),
    ),
    (
        "extinction",
        "Extinction",
        "strong_evidence",
        "Hunting and habitat loss in the 19th century are the documented drivers of the southern subspecies’ disappearance.",
        (C.HIGUCHI_1984_QUAGGA,),
        (),
    ),
    (
        "paleogenomics",
        "Paleogenomics",
        "strong_evidence",
        "Museum skins have yielded authentic DNA. Nuclear data exist in later studies; BioWiki only stores accessions that pass ingest validation.",
        (C.HIGUCHI_1984_QUAGGA,),
        (),
    ),
    ("significance", "Scientific importance", "consensus", "The quagga is a textbook case of subspecies extinction and of the first extinct-organism DNA.", (C.HIGUCHI_1984_QUAGGA,), ()),
    ("modern", "Why it matters now", "consensus", "The Quagga Project breeds plains zebras for a quagga-like stripe pattern; that is a phenotypic proxy, not E. q. quagga resurrected.", (), ()),
    ("deextinction", "De-extinction / restoration", "supported_hypothesis", "Selective breeding of Equus quagga is ongoing in South Africa. It does not recreate the extinct subspecies’ full genome.", (), ()),
)

NARRATIVES["ectopistes-migratorius"] = _claims(
    (
        "overview",
        "Overview",
        "consensus",
        "Ectopistes migratorius, the passenger pigeon, was a North American columbid that went extinct when Martha died in 1914.",
        (C.MURRAY_2017_PASSENGER_PIGEON,),
        (),
    ),
    (
        "evolution",
        "Evolution",
        "strong_evidence",
        "Genomes place it among New World pigeons. Extreme historical abundance was a derived ecological state, not proof of genetic invulnerability.",
        (C.MURRAY_2017_PASSENGER_PIGEON,),
        (),
    ),
    (
        "range",
        "Time and geographic range",
        "consensus",
        "The species occupied eastern North America, with enormous flocks before 19th-century collapse.",
        (C.MURRAY_2017_PASSENGER_PIGEON,),
        (),
    ),
    (
        "ecology",
        "Life and ecology",
        "strong_evidence",
        "It was a colonial, nomadic consumer of mast. Genomic diversity patterns have been used to discuss how selection and demography interacted before extinction.",
        (C.MURRAY_2017_PASSENGER_PIGEON,),
        (),
    ),
    (
        "extinction",
        "Extinction",
        "strong_evidence",
        "Industrial hunting and habitat conversion in the 19th century are documented. Genomic papers discuss whether low effective population size preceded the crash; that is additional, not a replacement for hunting as a proximate cause.",
        (C.MURRAY_2017_PASSENGER_PIGEON,),
        (),
    ),
    (
        "paleogenomics",
        "Paleogenomics",
        "consensus",
        "Museum specimens have yielded nuclear genomes used to estimate demography. These are not billions of SRA reads stored as Sequence rows.",
        (C.MURRAY_2017_PASSENGER_PIGEON,),
        (),
    ),
    ("significance", "Scientific importance", "consensus", "It is a primary case of anthropogenic extinction of a formerly hyper-abundant vertebrate.", (C.MURRAY_2017_PASSENGER_PIGEON,), ()),
    ("modern", "Why it matters now", "consensus", "Passenger pigeon genomics informs how quickly abundance can collapse and feeds de-extinction discussions that remain speculative.", (), ()),
    ("deextinction", "De-extinction / restoration", "supported_hypothesis", "Revive & Restore and others have discussed passenger pigeon work. No living Ectopistes exists.", (), ()),
)

NARRATIVES["hydrodamalis-gigas"] = _claims(
    (
        "overview",
        "Overview",
        "consensus",
        "Hydrodamalis gigas (Steller's sea cow) was a giant sirenian of the North Pacific, described by Steller in 1741 and extinct by 1768 in the Commander Islands.",
        (C.SHARKO_2021_STELLER,),
        (),
    ),
    (
        "evolution",
        "Evolution",
        "strong_evidence",
        "A published genome suggests the species had already declined before Paleolithic humans reached the region, in addition to the historically documented 18th-century hunt.",
        (C.SHARKO_2021_STELLER,),
        (),
    ),
    (
        "range",
        "Time and geographic range",
        "strong_evidence",
        "The last population occupied the Commander Islands. Pre-contact range reduction is a separate, earlier process discussed in genomic work.",
        (C.SHARKO_2021_STELLER,),
        (),
    ),
    (
        "ecology",
        "Life and ecology",
        "strong_evidence",
        "It grazed kelp and nearshore macroalgae. Loss of this grazer is relevant to kelp-forest history in the North Pacific.",
        (C.SHARKO_2021_STELLER,),
        (),
    ),
    (
        "extinction",
        "Extinction",
        "strong_evidence",
        "Intensive hunting after Bering’s 1741 landfall is historically documented as the proximate cause of the last population’s destruction. Genomic data add a longer-term decline hypothesis.",
        (C.SHARKO_2021_STELLER,),
        (),
    ),
    (
        "paleogenomics",
        "Paleogenomics",
        "strong_evidence",
        "Bone specimens have yielded a genome. Sample sizes remain small.",
        (C.SHARKO_2021_STELLER,),
        (),
    ),
    ("significance", "Scientific importance", "consensus", "It shows how quickly a marine megaherbivore can be extirpated after first industrial contact, against a longer demographic backdrop.", (C.SHARKO_2021_STELLER,), ()),
    ("modern", "Why it matters now", "consensus", "Sirenian conservation and kelp-ecosystem restoration use this extinction as a caution, not a template for resurrection.", (), ()),
    ("deextinction", "De-extinction / restoration", "consensus", "No active genomic resurrection programme is documented for H. gigas.", (), ()),
)

NARRATIVES["pinguinus-impennis"] = _claims(
    (
        "overview",
        "Overview",
        "consensus",
        "Pinguinus impennis, the great auk, was a flightless North Atlantic alcid. It is unrelated to penguins despite the shared vernacular root.",
        (C.THOMAS_2019_GREAT_AUK,),
        (),
    ),
    (
        "evolution",
        "Evolution",
        "strong_evidence",
        "It is nested within Alcidae. Flightlessness evolved in a diving lineage.",
        (C.THOMAS_2019_GREAT_AUK,),
        (),
    ),
    (
        "range",
        "Time and geographic range",
        "strong_evidence",
        "It nested on isolated North Atlantic islands. The last generally accepted breeding pair was killed on Eldey, Iceland, in 1844.",
        (C.THOMAS_2019_GREAT_AUK,),
        (),
    ),
    (
        "ecology",
        "Life and ecology",
        "strong_evidence",
        "Colonial nesting made it vulnerable to harvesting of eggs and adults.",
        (C.THOMAS_2019_GREAT_AUK,),
        (),
    ),
    (
        "extinction",
        "Extinction",
        "strong_evidence",
        "Ancient DNA supports rapid extinction under human hunting. Museum collecting contributed at the end; earlier commercial exploitation reduced the species.",
        (C.THOMAS_2019_GREAT_AUK,),
        (),
    ),
    (
        "paleogenomics",
        "Paleogenomics",
        "strong_evidence",
        "Museum skins and bones have produced mitochondrial data used for demographic reconstruction.",
        (C.THOMAS_2019_GREAT_AUK,),
        (),
    ),
    ("significance", "Scientific importance", "consensus", "The great auk is a documented case of extinction driven by hunting of a colonial seabird.", (C.THOMAS_2019_GREAT_AUK,), ()),
    ("modern", "Why it matters now", "consensus", "Seabird conservation still contends with harvest, introduced predators, and museum/scientific collecting ethics.", (), ()),
    ("deextinction", "De-extinction / restoration", "consensus", "No genomic resurrection of P. impennis has been achieved.", (), ()),
)

NARRATIVES["dinornis-robustus"] = _claims(
    (
        "overview",
        "Overview",
        "consensus",
        "Dinornis robustus is the South Island giant moa, a flightless palaeognath of New Zealand (NCBI TaxID 314500). Other moa genera existed; this profile is this taxon, not all moa, and not a claim that Dinornis has been returned to life.",
        (C.BUNCE_2003_DINORNIS,),
        (),
    ),
    (
        "evolution",
        "Evolution",
        "strong_evidence",
        "Ancient DNA demonstrated extreme reversed sexual size dimorphism in Dinornis: large and small morphs were sexes, not separate species. Flightlessness evolved in the New Zealand palaeognath radiation, not as a designed outcome.",
        (C.BUNCE_2003_DINORNIS,),
        (),
    ),
    (
        "range",
        "Time and geographic range",
        "strong_evidence",
        "South Island, New Zealand. Extinction followed Polynesian settlement in the late Holocene.",
        (C.BUNCE_2003_DINORNIS, C.HOLDAWAY_2000_MOA_EXTINCTION),
        (),
    ),
    (
        "ecology",
        "Life and ecology",
        "strong_evidence",
        "They were herbivores whose browsing is reconstructed from palaeoecology and morphology. Extreme sexual size dimorphism is genetically confirmed. Hypothesized ecosystem roles if an analogue were introduced today are not observations of living Dinornis.",
        (C.BUNCE_2003_DINORNIS,),
        (),
    ),
    (
        "extinction",
        "Extinction",
        "strong_evidence",
        "Polynesian settlement, hunting, and associated landscape fire are the supported drivers. Holdaway and Jacomb 2000 modelled rapid extinction after human arrival. Allentoft et al. 2014 argued that a low-density human population was sufficient to exterminate moa. Present the literature rather than a slogan; timing and kill-rate models remain refined, but human-driven loss is strongly supported.",
        (C.BUNCE_2003_DINORNIS, C.HOLDAWAY_2000_MOA_EXTINCTION, C.ALLENTOFT_2014_MOA_EXTERMINATION),
        (),
    ),
    (
        "paleogenomics",
        "Paleogenomics",
        "consensus",
        "Excellent preservation in New Zealand caves yielded mitochondrial and nuclear data for moa. Public nuccore for TaxID 314500 is larger than this collection’s preferred discovery goal; BioWiki stored a curated subset as Sequence rows and does not treat extra fragments as a quota to fill.",
        (C.BUNCE_2003_DINORNIS,),
        (),
    ),
    (
        "significance",
        "Scientific importance",
        "consensus",
        "Moa DNA rebuilt palaeognath taxonomy of size morphs and documented human-driven megafaunal loss on islands.",
        (C.BUNCE_2003_DINORNIS,),
        (),
    ),
    (
        "modern",
        "Why it matters now",
        "consensus",
        "New Zealand restoration ecology uses moa as a missing herbivore guild; that is palaeoecological history, not proof that a proxy bird would restore pre-human vegetation. Company de-extinction language must be separated from that ecological literature.",
        (C.ALLENTOFT_2014_MOA_EXTERMINATION,),
        (),
    ),
    (
        "deextinction",
        "De-extinction / restoration",
        "supported_hypothesis",
        """
Independent news (including AP) and Colossal Biosciences’ own programme pages
report an announced South Island giant moa research effort with partners in
New Zealand, using living palaeognaths as genomic chassis. That is an active
research programme as organization-reported and as covered by independent news.
It is not peer-reviewed evidence that Dinornis robustus has been resurrected.
A May 2026 Nature news article discussed synthetic-egg / avian incubation
technology in the context of extinct birds including dodo and moa and explicitly
urged caution about what the demonstration shows. Company-reported hatching of
chickens in an artificial eggshell is not independent proof of a moa embryo,
nor of a returned historical species. BioWiki therefore records status as an
active research programme, not reproductive-technology demonstration at moa
scale, and never as resurrection.
""",
        (C.NATURE_2026_SYNTHETIC_EGG,),
        (C.NATURE_2026_SYNTHETIC_EGG_DOI,),
        (
            C.COLOSSAL_MOA_PROGRAMME_URL,
            C.AP_2025_MOA_PROGRAMME_URL,
        ),
    ),
    (
        "uncertainty",
        "Uncertainties / debates",
        "debated",
        """
Kill-rate and duration-of-extinction models differ among papers even where
human causation is agreed. Company avian reproductive milestones remain
organization-reported until independently published. A genetically modified
living relative would not automatically be Dinornis robustus.
""",
        (C.HOLDAWAY_2000_MOA_EXTINCTION, C.NATURE_2026_SYNTHETIC_EGG),
        (),
    ),
)

NARRATIVES["megaloceros-giganteus"] = _claims(
    (
        "overview",
        "Overview",
        "consensus",
        "Megaloceros giganteus (Irish elk / giant deer) was a large Pleistocene cervid of Eurasia. ‘Irish’ is a historical collection bias, not a geographic restriction.",
        (C.LISTER_2005_MEGALOCEROS,),
        (),
    ),
    (
        "evolution",
        "Evolution",
        "strong_evidence",
        "Ancient DNA allies it with fallow deer (Dama) rather than with Cervus as once assumed from antler form.",
        (C.LISTER_2005_MEGALOCEROS,),
        (),
    ),
    (
        "range",
        "Time and geographic range",
        "strong_evidence",
        "It occupied open and mosaic habitats across Eurasia. Populations persisted into the Holocene in some regions.",
        (C.LISTER_2005_MEGALOCEROS,),
        (),
    ),
    (
        "ecology",
        "Life and ecology",
        "supported_hypothesis",
        "Diet was that of a large mixed feeder. Whether antlers constrained forest use is debated.",
        (C.LISTER_2005_MEGALOCEROS,),
        (),
    ),
    (
        "extinction",
        "Extinction",
        "debated",
        "Climate, vegetation change, and humans are all invoked. A single antler-maladaptation story is insufficient.",
        (C.LISTER_2005_MEGALOCEROS,),
        (),
    ),
    (
        "paleogenomics",
        "Paleogenomics",
        "strong_evidence",
        "Mitochondrial sequences from bone are published. Nuclear data are sparser than for horses or bison.",
        (C.LISTER_2005_MEGALOCEROS,),
        (),
    ),
    ("significance", "Scientific importance", "consensus", "It is a test case for sexual selection, allometry, and Late Quaternary cervid loss.", (C.LISTER_2005_MEGALOCEROS,), ()),
    ("modern", "Why it matters now", "consensus", "Giant-deer extinction is used in debates on whether spectacular traits increase extinction risk — still a hypothesis.", (), ()),
    ("deextinction", "De-extinction / restoration", "consensus", "No active genomic resurrection programme is documented.", (), ()),
)

NARRATIVES["ursus-spelaeus"] = _claims(
    (
        "overview",
        "Overview",
        "consensus",
        "Ursus spelaeus, the cave bear, was a Late Pleistocene ursid of Europe, genetically distinct from living brown bears (Ursus arctos).",
        (C.FORTES_2016_CAVE_BEAR, C.GREENWOOD_1999_MEGAFAUNA_NUCLEAR),
        (),
    ),
    (
        "evolution",
        "Evolution",
        "strong_evidence",
        "Cave bears form a clade with brown bears but are a separate species. Late Pleistocene nuclear DNA from megafauna, including bears, was among the early ancient-DNA nuclear datasets.",
        (C.GREENWOOD_1999_MEGAFAUNA_NUCLEAR,),
        (),
    ),
    (
        "range",
        "Time and geographic range",
        "strong_evidence",
        "European caves yield abundant remains. Disappearance is Late Pleistocene.",
        (C.FORTES_2016_CAVE_BEAR,),
        (),
    ),
    (
        "ecology",
        "Life and ecology",
        "strong_evidence",
        "Ancient DNA and isotopes have been used to compare cave-bear and brown-bear behaviour and sociality. Cave bears were not simply ‘big brown bears in caves’.",
        (C.FORTES_2016_CAVE_BEAR,),
        (),
    ),
    (
        "extinction",
        "Extinction",
        "debated",
        "Disappearance around the Last Glacial Maximum has been linked to climate, habitat, and possible human competition for caves.",
        (C.FORTES_2016_CAVE_BEAR,),
        (),
    ),
    (
        "paleogenomics",
        "Paleogenomics",
        "consensus",
        "Cave deposits yielded some of the first high-coverage ancient mammalian genomes. Mitogenomes are numerous.",
        (C.FORTES_2016_CAVE_BEAR, C.GREENWOOD_1999_MEGAFAUNA_NUCLEAR),
        (),
    ),
    ("significance", "Scientific importance", "consensus", "Cave bear DNA helped establish authenticity criteria for ancient DNA.", (C.GREENWOOD_1999_MEGAFAUNA_NUCLEAR,), ()),
    ("modern", "Why it matters now", "consensus", "It remains a model for how herbivorous megafauna respond to glacial maxima and human niche overlap.", (), ()),
    ("deextinction", "De-extinction / restoration", "consensus", "No programme claims to have resurrected U. spelaeus.", (), ()),
)
