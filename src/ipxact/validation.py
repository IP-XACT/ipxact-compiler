"""Optional validation of IP-XACT documents against the IEEE 1685-2022 XSD shipped with this package."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Union

from lxml import etree

_XSD_DIR = Path(__file__).parent / "xsd" / "1685-2022"


def xsd_path() -> Path:
    """The folder holding the shipped IEEE 1685-2022 XSD files (entry point: ``index.xsd``)."""
    return _XSD_DIR


@dataclass(frozen=True)
class ValidationIssue:
    """One XSD validation error, at a line/column of the validated document."""

    line: int
    column: int
    message: str

    def __str__(self) -> str:
        return f"line {self.line}: {self.message}"


class ValidationError(ValueError):
    """Raised by ``parse_file(..., validate=True)`` when the document is not valid against the XSD."""

    def __init__(self, issues: list[ValidationIssue]):
        self.issues = issues
        super().__init__(f"{len(issues)} XSD validation error(s), first: {issues[0]}")


@lru_cache(maxsize=None)
def _schema() -> etree.XMLSchema:
    # index.xsd includes the schema of every IP-XACT document type
    return etree.XMLSchema(etree.parse(str(_XSD_DIR / "index.xsd")))


def validate(source: Union[str, Path, etree._ElementTree, etree._Element]) -> list[ValidationIssue]:
    """Validate an IP-XACT document against the IEEE 1685-2022 XSD; an empty list means valid.

    ``source`` is a file path, or an already parsed lxml tree or root element (for example the
    output of an exporter, before writing it).
    """
    document = etree.parse(str(source)) if isinstance(source, (str, Path)) else source
    schema = _schema()
    schema.validate(document)
    # lxml-stubs do not declare _ErrorLog iterable, although it is
    errors = schema.error_log
    return [ValidationIssue(e.line, e.column, e.message) for e in errors]  # type: ignore[attr-defined]
