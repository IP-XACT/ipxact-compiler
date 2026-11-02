from __future__ import annotations

from lxml import etree

from ..schema.busdefinition import BusDefinition
from .common_parser import (
    bool_text,
    child,
    expr,
    parse_assertions,
    parse_children,
    parse_choices,
    parse_name_group,
    parse_parameters,
    parse_vendor_extensions,
    parse_vlnv,
    parse_vlnv_ref,
    text_value,
    xml_id,
)


def parse_busdefinition(root: etree._Element) -> BusDefinition:
    """Parse an ipxact:busDefinition root element into a BusDefinition object."""
    extends_elem = child(root, "extends")
    return BusDefinition(
        vlnv=parse_vlnv(root),
        direct_connection=bool_text(root, "directConnection", False),
        is_addressable=bool_text(root, "isAddressable", False),
        broadcast=bool_text(root, "broadcast"),
        extends=parse_vlnv_ref(extends_elem) if extends_elem is not None else None,
        max_initiators=expr(root, "maxInitiators"),
        max_targets=expr(root, "maxTargets"),
        system_group_names=parse_children(root, "systemGroupNames", "systemGroupName", text_value),
        choices=parse_choices(root),
        parameters=parse_parameters(root),
        assertions=parse_assertions(root),
        **parse_name_group(root),
        xml_id=xml_id(root),
        vendor_extensions=parse_vendor_extensions(root),
    )
