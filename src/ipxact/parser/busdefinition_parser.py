from __future__ import annotations

from lxml import etree

from ..schema.busdefinition import BusDefinition


def parse_busdefinition(root: etree._Element) -> BusDefinition:
    """Parse an ipxact:busDefinition root element into a BusDefinition object."""
    raise NotImplementedError
