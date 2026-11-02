__version__ = "0.2.0"

from .parser import parse_element, parse_file
from .schema import *  # noqa: F401,F403
from .schema import __all__ as _schema_all
from .validation import ValidationError, ValidationIssue, validate, xsd_path

__all__ = [
    *_schema_all,
    "parse_element",
    "parse_file",
    "validate",
    "xsd_path",
    "ValidationError",
    "ValidationIssue",
    "__version__",
]
