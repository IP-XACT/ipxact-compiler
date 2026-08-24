from __future__ import annotations

from lxml import etree

from ..schema.design import Design


def parse_design(root: etree._Element) -> Design:
    """Parse an ipxact:design root element into a Design object."""
    raise NotImplementedError
