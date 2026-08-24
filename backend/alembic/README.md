# Alembic (BioWiki)

Schema for a **clean PostgreSQL** is created by the initial revision
`0004_publication_abstract`. That identifier matches databases that were
already stamped before these files lived in git, so `alembic upgrade head`
is a no-op on an existing catalogue and a full create on an empty database.

From `backend/` with the virtualenv active and `DATABASE_URL` set:

```bash
python -m alembic upgrade head
```

Required PostgreSQL extensions (created by the migration): `pgcrypto`, `pg_trgm`.

Do not point Alembic at a database that already holds scientific rows unless
it is already stamped at `0004_publication_abstract`. Never dump the live
corpus into git.
