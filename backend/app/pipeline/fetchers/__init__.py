"""Source fetchers: connector → parser/builder → validated import.

One module per public database. Every fetcher:
- downloads real records through the resilient connector layer,
- normalises them into the pipeline IR (never inventing values),
- persists them through the validated importers,
- and records the execution in ``ingestion_runs``.

Nothing runs automatically — fetchers are invoked explicitly (CLI or code).
"""

from app.pipeline.fetchers.base import import_with_run

__all__ = ["import_with_run"]
