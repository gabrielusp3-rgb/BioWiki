"""Data ingestion pipeline.

Parses, validates and persists **real** biological sequences obtained from
official sources (via the connector layer or files exported from those sources).
No fictitious data is ever generated: records that fail validation are logged and
skipped, never invented or completed with placeholder values.

Flow:  parse → validate → persist  (orchestrated by the import worker)
"""

from app.pipeline.errors import (
    PipelineError,
    ImportPersistenceError,
    ParseError,
    ValidationError,
)
from app.pipeline.models import (
    ImportContext,
    ImportReport,
    ParsedOrganism,
    ParsedSequence,
    ParsedXref,
)

__all__ = [
    "PipelineError",
    "ParseError",
    "ValidationError",
    "ImportPersistenceError",
    "ImportContext",
    "ImportReport",
    "ParsedOrganism",
    "ParsedSequence",
    "ParsedXref",
]
