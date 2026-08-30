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

- Introgression rows are gene-level published associations. Coordinates are omitted unless a cited paper and genome build are stored.
- Public nuccore diversity is small for several historic extinctions (for example *Raphus cucullatus*). Validated count may be far below the preferred target.
- *Homo floresiensis*, *Homo naledi* and *Homo erectus* are noted as lacking authentic public ancient DNA in this catalogue; no sequence records are invented for them.
- Company de-extinction statements are classified as organisation-reported progress, not peer-reviewed resurrection.
- Controlled-access genomic datasets are metadata-only.

Catalogue counts belong in the README only after a production ingest, using live numbers.
