from __future__ import annotations

from pathlib import Path
from typing import Union

from lxml import etree

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


def parse_file(path: Union[str, Path]):
    """Parse an IP-XACT XML file, dispatching on its root element to the matching parser.

    Comments are stripped during parsing.. If left in place, it pushes a following value onto
    the comment's ``.tail`` instead of the parent's ``.text``,
    so field's default value with no error, which is a problem.
    """
    root = etree.parse(str(path), parser=_XML_PARSER).getroot()
    return parse_element(root)


def parse_element(root: etree._Element):
    """Parse an already-loaded IP-XACT root element, dispatching to the matching parser."""
    try:
        parser = _ROOT_TAG_PARSERS[root.tag]
    except KeyError:
        raise ValueError(f"unrecognized IP-XACT root element: {root.tag!r}") from None
    return parser(root)
