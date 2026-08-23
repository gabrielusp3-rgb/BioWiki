# Security

BioWiki is a read-only catalogue over a local PostgreSQL database. The HTTP API does not ingest data.

## Reporting

Do not open a public issue for a vulnerability that could expose the database, credentials, or a way to write scientific records.

After the project is on GitHub, use **Security → Report a vulnerability** (a private advisory on this repository).

There is no dedicated security team and no guaranteed response time. Reports are reviewed as time allows.

## Scope

In scope: the BioWiki application code in this repository (FastAPI, Next.js, CLI).

Out of scope: NCBI, UniProt, Ensembl, PDB, ENA, Rfam, PubMed, and other upstream services; your own `.env` and PostgreSQL deployment.

## Secrets

Never commit `.env`, `.env.local`, API keys, or database URLs. Use the `.env.example` files as templates.
