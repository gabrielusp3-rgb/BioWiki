"""Pipeline error hierarchy."""

from __future__ import annotations


class PipelineError(Exception):
    """Base class for pipeline failures."""


class ParseError(PipelineError):
    """A source document could not be parsed."""


class ValidationError(PipelineError):
    """A parsed record failed validation and must not be persisted."""

    def __init__(self, message: str, *, field: str | None = None) -> None:
        super().__init__(message)
        self.field = field


class ImportPersistenceError(PipelineError):
    """A validated record could not be persisted to the database."""
