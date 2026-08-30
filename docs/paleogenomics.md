# Paleogenomics collection

Paleogenomics is a **scientific collection** inside BioWiki. It is not a molecule type, not a second application, and not a `SequenceType`.

Ancient specimen DNA remains `dna` (or `rna` / `protein` when that is the authentic molecule). Genome assemblies remain `genome_records`. Introgression intervals in living *Homo sapiens* are stored in `paleogenomic_introgression_regions` and must never be presented as DNA extracted from an archaic bone.

## Schema

Alembic revision `0007_paleogenomics` adds:

- optional `organisms.extinction_status`, `extinction_date_text`, `geologic_period` (living taxa keep these NULL)
- `paleogenomic_profiles` (1:1 with `organisms`)
- `paleogenomic_claims` + `paleogenomic_claim_sources` (deterministic, reviewed narrative; no runtime LLM)
- `paleogenomic_sequence_membership` (unique `sequence_id`)
- `paleogenomic_projects` (BioProject / BioSample / run **metadata**, never raw reads as Sequence rows)
- `paleogenomic_introgression_regions` (modern TaxID 9606)
- `paleogenomic_publication_membership` (profile ↔ existing `publications`; 1 PMID = 1 Publication)

Evidence levels: `consensus`, `strong_evidence`, `supported_hypothesis`, `debated`, `unknown`.

De-extinction status is **not** an evidence level. A genetically engineered proxy is not the historical organism. BioWiki does not use a `resurrected` status.

## Ingest

Species-oriented, checkpointed, additive:

```bash
python -m app.pipeline.cli paleogenomics --seed-only
python -m app.pipeline.cli paleogenomics --discover-only
python -m app.pipeline.cli paleogenomics
python -m app.pipeline.cli paleogenomics --relink-literature --ingest-projects
```

Natural key remains `source + accession + version`. TaxID must match the locked NCBI identifiers in `app/pipeline/paleogenomics/catalogue.py`. Preferred sequence targets are discovery goals, not quotas. Chromosome-scale residues are rejected; assemblies go to `genome_records`. SRA run accessions are not Sequence rows.

Checkpoint: `backend/data/paleogenomics_checkpoint.json` (gitignored). Discovery report: `backend/data/paleogenomics_discovery.json` (gitignored).

## API

- `GET /paleogenomics`
- `GET /paleogenomics/statistics`
- `GET /paleogenomics/species`
- `GET /paleogenomics/species/{slug}`
- nested paginated `sequences`, `publications`, `genomes`, `projects`
- `GET /paleogenomics/introgression`

Search (`GET /search`) returns `paleogenomicsProfiles` in addition to sequences and publications.

## Limitations

- Introgression rows are gene-level published associations. Coordinates are omitted unless a cited paper and genome build are stored. Nine loci are curated (Neanderthal and Denisovan sources). That is not ~200 invented genomic intervals.
- Public nuccore diversity is small for several historic extinctions. *Raphus cucullatus* has four validated nuccore records (two complete mitogenomes that are GenBank/RefSeq equivalents, plus two partial Oxford voucher fragments). *Equus quagga quagga* has three. *Smilodon populator* has twelve. Counts stop at authentic records.
- NCBI Datasets/Assembly returned no assembly reports for Neanderthal (TaxID 63221) and woolly mammoth (TaxID 37349). High-coverage genomes exist as BioProjects/SRA; BioWiki stores BioProject metadata, not raw reads and not invented GCA accessions. A few collection organisms do have `genome_records` (thylacine, Steller's sea cow, giant deer).
- Neanderthal nuccore includes many short genomic survey (GSS) library fragments alongside mitochondrial records. Later discovery excludes GSS/patent filters so additional species are not filled the same way. Existing GSS rows were not bulk-deleted.
- Complete-mitogenome flags require both an appropriate length and a complete-genome definition. NCBI titles such as “mitochondrion, complete genome” are accepted; partial cytb/12S fragments are not promoted.
- *Homo floresiensis*, *Homo naledi* and *Homo erectus* are noted as lacking authentic public ancient DNA in this catalogue; no sequence records are invented for them.
- Company de-extinction statements are classified as organisation-reported progress, not peer-reviewed resurrection. A genetically engineered proxy is not the historical organism.
- Controlled-access genomic datasets are metadata-only.

Production counts after ingest belong in the README.
