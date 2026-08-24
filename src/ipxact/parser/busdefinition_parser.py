from __future__ import annotations

from lxml import etree

from ..schema.busdefinition import BusDefinition
from .common_parser import (
    bool_text,
    child,
    parse_assertions,
    parse_choices,
    parse_parameters,
    parse_vendor_extensions,
    parse_vlnv,
    parse_vlnv_ref,
    text,
    texts,
)


def parse_busdefinition(root: etree._Element) -> BusDefinition:
    """Parse an ipxact:busDefinition root element into a BusDefinition object."""
    extends_elem = child(root, "extends")
    system_group_names_container = child(root, "systemGroupNames")
    return BusDefinition(
        vlnv=parse_vlnv(root),
        direct_connection=bool_text(root, "directConnection", False),
        is_addressable=bool_text(root, "isAddressable", False),
        broadcast=bool_text(root, "broadcast"),
        extends=parse_vlnv_ref(extends_elem) if extends_elem is not None else None,
        max_initiators=text(root, "maxInitiators"),
        max_targets=text(root, "maxTargets"),
        system_group_names=(
            texts(system_group_names_container, "systemGroupName")
            if system_group_names_container is not None
            else []
        ),
        choices=parse_choices(root),
        parameters=parse_parameters(root),
        assertions=parse_assertions(root),
        display_name=text(root, "displayName"),
        short_description=text(root, "shortDescription"),
        description=text(root, "description"),
        vendor_extensions=parse_vendor_extensions(root),
    )
