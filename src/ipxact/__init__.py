from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _version

from .parser import parse_element, parse_file
from .schema import *  # noqa: F401,F403
from .schema import __all__ as _schema_all

try:
    __version__ = _version("ipxact-compiler")
except PackageNotFoundError:
    __version__ = "0.0.0+unknown"

__all__ = [*_schema_all, "parse_element", "parse_file", "__version__"]
