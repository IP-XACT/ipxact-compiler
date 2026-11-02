from __future__ import annotations

from lxml import etree

from ..schema.abstractiondefinition import (
    AbstractionDefinition,
    AbstractionPort,
    Packet,
    PacketField,
    PortConstraints,
    Presence,
    RequiresDriver,
    TransactionalAbstractionPort,
    TransactionalModeConstraints,
    TransactionalSystemConstraints,
    WireAbstractionPort,
    WireModeConstraints,
    WireSystemConstraints,
)
from .common_parser import (
    as_bool,
    attr_bool,
    bool_text,
    child,
    children,
    elem_text,
    expr,
    parse_assertions,
    parse_children,
    parse_choices,
    parse_drive_constraint,
    parse_optional_expression,
    parse_load_constraint,
    parse_name_group,
    parse_parameters,
    parse_protocol,
    parse_qualifier,
    parse_timing_constraints,
    parse_vendor_extensions,
    parse_vlnv,
    parse_vlnv_ref,
    required_expr,
    text,
    xml_id,
)


def parse_abstractiondefinition(root: etree._Element) -> AbstractionDefinition:
    """Parse an ipxact:abstractionDefinition root element into an AbstractionDefinition object."""
    extends_elem = child(root, "extends")
    return AbstractionDefinition(
        vlnv=parse_vlnv(root),
        bus_type=parse_vlnv_ref(child(root, "busType")),
        extends=parse_vlnv_ref(extends_elem) if extends_elem is not None else None,
        ports=parse_children(root, "ports", "port", _parse_abstraction_port),
        choices=parse_choices(root),
        parameters=parse_parameters(root),
        assertions=parse_assertions(root),
        **parse_name_group(root),
        xml_id=xml_id(root),
        vendor_extensions=parse_vendor_extensions(root),
    )


def _parse_port_constraints(elem: etree._Element) -> PortConstraints:
    return PortConstraints(
        timing_constraints=parse_timing_constraints(elem),
        drive_constraint=parse_drive_constraint(elem),
        load_constraint=parse_load_constraint(elem),
    )


def _parse_requires_driver(elem: etree._Element) -> RequiresDriver:
    return RequiresDriver(value=as_bool(elem_text(elem), False), driver_type=elem.get("driverType", "any"))


def _parse_wire_mode_constraints(elem: etree._Element) -> WireModeConstraints:
    presence = text(elem, "presence")
    width_elem = child(elem, "width")
    direction_elem = child(elem, "direction")
    mode_constraints_elem = child(elem, "modeConstraints")
    mirrored_mode_constraints_elem = child(elem, "mirroredModeConstraints")
    return WireModeConstraints(
        presence=Presence(presence) if presence else Presence.OPTIONAL,
        width=parse_optional_expression(width_elem),
        width_all_bits_required=attr_bool(width_elem, "allBits", False) if width_elem is not None else False,
        # default to out and missing means no restiction, so None.
        direction=(elem_text(direction_elem) or "out") if direction_elem is not None else None,
        mode_constraints=(
            _parse_port_constraints(mode_constraints_elem) if mode_constraints_elem is not None else None
        ),
        mirrored_mode_constraints=(
            _parse_port_constraints(mirrored_mode_constraints_elem)
            if mirrored_mode_constraints_elem is not None
            else None
        ),
    )


def _parse_wire_system_constraints(elem: etree._Element) -> WireSystemConstraints:
    return WireSystemConstraints(
        group=text(elem, "group") or "", constraints=_parse_wire_mode_constraints(elem), xml_id=xml_id(elem)
    )


def _parse_wire_abstraction_port(elem: etree._Element) -> WireAbstractionPort:
    on_initiator_elem = child(elem, "onInitiator")
    on_target_elem = child(elem, "onTarget")
    requires_driver_elem = child(elem, "requiresDriver")
    return WireAbstractionPort(
        qualifier=parse_qualifier(elem),
        on_system=[_parse_wire_system_constraints(e) for e in children(elem, "onSystem")],
        on_initiator=_parse_wire_mode_constraints(on_initiator_elem) if on_initiator_elem is not None else None,
        on_target=_parse_wire_mode_constraints(on_target_elem) if on_target_elem is not None else None,
        default_value=expr(elem, "defaultValue"),
        requires_driver=_parse_requires_driver(requires_driver_elem) if requires_driver_elem is not None else None,
    )


def _parse_transactional_mode_constraints(elem: etree._Element) -> TransactionalModeConstraints:
    presence = text(elem, "presence")
    initiative_elem = child(elem, "initiative")
    kind_elem = child(elem, "kind")
    return TransactionalModeConstraints(
        presence=Presence(presence) if presence else Presence.OPTIONAL,
        # Same rule as <direction>: missing means "not restricted", default is "requires".
        initiative=(elem_text(initiative_elem) or "requires") if initiative_elem is not None else None,
        kind=elem_text(kind_elem),
        kind_custom=kind_elem.get("custom") if kind_elem is not None else None,
        bus_width=expr(elem, "busWidth"),
        protocol=parse_protocol(elem),
    )


def _parse_transactional_system_constraints(elem: etree._Element) -> TransactionalSystemConstraints:
    return TransactionalSystemConstraints(
        group=text(elem, "group") or "", constraints=_parse_transactional_mode_constraints(elem), xml_id=xml_id(elem)
    )


def _parse_transactional_abstraction_port(elem: etree._Element) -> TransactionalAbstractionPort:
    on_initiator_elem = child(elem, "onInitiator")
    on_target_elem = child(elem, "onTarget")
    return TransactionalAbstractionPort(
        qualifier=parse_qualifier(elem),
        on_system=[_parse_transactional_system_constraints(e) for e in children(elem, "onSystem")],
        on_initiator=(
            _parse_transactional_mode_constraints(on_initiator_elem) if on_initiator_elem is not None else None
        ),
        on_target=_parse_transactional_mode_constraints(on_target_elem) if on_target_elem is not None else None,
    )


def _parse_packet_field(elem: etree._Element) -> PacketField:
    return PacketField(
        name=text(elem, "name") or "",
        width=required_expr(elem, "width"),
        value=expr(elem, "value"),
        endianness=text(elem, "endianness"),
        qualifier=parse_qualifier(elem),
        **parse_name_group(elem),
        xml_id=xml_id(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_packet(elem: etree._Element) -> Packet:
    return Packet(
        name=text(elem, "name") or "",
        packet_fields=parse_children(elem, "packetFields", "packetField", _parse_packet_field),
        endianness=text(elem, "endianness"),
        **parse_name_group(elem),
        xml_id=xml_id(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_abstraction_port(elem: etree._Element) -> AbstractionPort:
    wire_elem = child(elem, "wire")
    transactional_elem = child(elem, "transactional")
    return AbstractionPort(
        logical_name=text(elem, "logicalName") or "",
        wire=_parse_wire_abstraction_port(wire_elem) if wire_elem is not None else None,
        transactional=(
            _parse_transactional_abstraction_port(transactional_elem) if transactional_elem is not None else None
        ),
        packets=parse_children(elem, "packets", "packet", _parse_packet),
        match=bool_text(elem, "match", False),
        **parse_name_group(elem),
        xml_id=xml_id(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )
