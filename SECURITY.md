# Security

BioWiki is a public scientific catalogue. The production HTTP API is read-only. Catalogue ingestion is CLI-only and is not exposed as a web endpoint.

## Supported versions

Security fixes are applied to the `main` branch that is deployed to:

- https://biowiki-nine.vercel.app
- https://biowiki-api.vercel.app

There is no long-term support branch besides `main`.

## Reporting a vulnerability

Do not open a public issue for a vulnerability that could expose the database, credentials, or a way to write scientific records. Do not include working exploit details in a public channel before a fix is available.

Use **GitHub Security → Report a vulnerability** (a private advisory on [gabrielusp3-rgb/BioWiki](https://github.com/gabrielusp3-rgb/BioWiki)).

There is no dedicated security team and no guaranteed response time. Reports are reviewed as time allows.

## Secrets

Never commit `.env`, `.env.local`, API keys, database URLs, or Vercel/GitHub tokens. Use `.env.example` as a template. Frontend `NEXT_PUBLIC_*` variables are visible in the browser by design; they must not contain backend secrets.

## Scope

In scope: BioWiki application code in this repository (FastAPI, Next.js, Docker, GitHub Actions, CLI).

Out of scope: NCBI, UniProt, Ensembl, PDB, ENA, Rfam, PubMed, Neon, Vercel, and other upstream or platform services; a reporter’s own `.env` files.
