"""Format → parser registry."""

from __future__ import annotations

from app.pipeline.errors import ParseError
from app.pipeline.parsers.base import BaseParser
from app.pipeline.parsers.csv_parser import CsvParser
from app.pipeline.parsers.fasta import FastaParser
from app.pipeline.parsers.genbank import GenBankParser
from app.pipeline.parsers.json_parser import JsonParser

_REGISTRY: dict[str, BaseParser] = {
    "fasta": FastaParser(),
    "fa": FastaParser(),
    "genbank": GenBankParser(),
    "gb": GenBankParser(),
    "gbk": GenBankParser(),
    "json": JsonParser(),
    "csv": CsvParser(),
}


def register_parser(fmt: str, parser: BaseParser) -> None:
    _REGISTRY[fmt.lower()] = parser


def get_parser(fmt: str) -> BaseParser:
    parser = _REGISTRY.get(fmt.lower())
    if parser is None:
        raise ParseError(f"No parser registered for format {fmt!r}.")
    return parser
