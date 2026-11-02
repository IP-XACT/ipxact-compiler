from __future__ import annotations

from pathlib import Path
from typing import Union

from lxml import etree

from .. import validation
from .abstractiondefinition_parser import parse_abstractiondefinition
from .busdefinition_parser import parse_busdefinition
from .common_parser import qn
from .component_parser import parse_component
from .design_parser import parse_design
from .designconfig_parser import parse_designconfig

_ROOT_TAG_PARSERS = {
    qn("component"): parse_component,
    qn("design"): parse_design,
    qn("designConfiguration"): parse_designconfig,
    qn("busDefinition"): parse_busdefinition,
    qn("abstractionDefinition"): parse_abstractiondefinition,
}


_XML_PARSER = etree.XMLParser(remove_comments=True)


def parse_file(path: Union[str, Path], validate: bool = False):
    """Parse an IP-XACT XML file, dispatching on its root element to the matching parser.

    Comments are stripped during parsing so they don't end up in the raw vendorExtensions
    strings. Text values are read the same way with or without comments (see elem_text), so
    parse_element() also works on a tree loaded with a default parser.

    With ``validate=True``, the file is first validated against the shipped IEEE 1685-2022 XSD
    and a ``ValidationError`` listing every problem is raised if it is not valid.
    """
    tree = etree.parse(str(path), parser=_XML_PARSER)
    if validate:
        issues = validation.validate(tree)
        if issues:
            raise validation.ValidationError(issues)
    return parse_element(tree.getroot())


def parse_element(root: etree._Element):
    """Parse an already-loaded IP-XACT root element, dispatching to the matching parser."""
    try:
        parser = _ROOT_TAG_PARSERS[root.tag]
    except KeyError:
        raise ValueError(f"unrecognized IP-XACT root element: {root.tag!r}") from None
    return parser(root)
