from __future__ import annotations

from lxml import etree

from ..schema.abstractiondefinition import AbstractionDefinition


def parse_abstractiondefinition(root: etree._Element) -> AbstractionDefinition:
    """Parse an ipxact:abstractionDefinition root element into an AbstractionDefinition object."""
    raise NotImplementedError
