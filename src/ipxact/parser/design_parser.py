from __future__ import annotations

from lxml import etree

from ..schema.design import (
    ActiveInterface,
    AdHocConnection,
    ComponentInstance,
    Design,
    ExternalPortReference,
    HierInterface,
    Interconnection,
    InternalPortReference,
    MonitorInterconnection,
    MonitorInterfaceRef,
    PowerDomainLink,
)
from .common_parser import (
    child,
    children,
    expr,
    parse_assertions,
    parse_children,
    parse_choices,
    parse_name_group,
    parse_parameters,
    parse_part_select,
    parse_sub_port_references,
    parse_vendor_extensions,
    parse_vlnv,
    parse_vlnv_ref,
    qn,
    required_expr,
    text,
    text_value,
    text_values,
    xml_id,
)


def parse_design(root: etree._Element) -> Design:
    """Parse an ipxact:design root element into a Design object."""
    interconnections_container = child(root, "interconnections")

    interconnections: list[Interconnection] = []
    monitor_interconnections: list[MonitorInterconnection] = []
    if interconnections_container is not None:
        for elem in interconnections_container:
            if elem.tag == qn("interconnection"):
                interconnections.append(_parse_interconnection(elem))
            elif elem.tag == qn("monitorInterconnection"):
                monitor_interconnections.append(_parse_monitor_interconnection(elem))

    return Design(
        vlnv=parse_vlnv(root),
        component_instances=parse_children(root, "componentInstances", "componentInstance", _parse_component_instance),
        interconnections=interconnections,
        monitor_interconnections=monitor_interconnections,
        ad_hoc_connections=parse_children(root, "adHocConnections", "adHocConnection", _parse_ad_hoc_connection),
        choices=parse_choices(root),
        parameters=parse_parameters(root),
        assertions=parse_assertions(root),
        **parse_name_group(root),
        xml_id=xml_id(root),
        vendor_extensions=parse_vendor_extensions(root),
    )


def _parse_power_domain_link(elem: etree._Element) -> PowerDomainLink:
    return PowerDomainLink(
        external_power_domain_ref=required_expr(elem, "externalPowerDomainReference"),
        internal_power_domain_refs=text_values(elem, "internalPowerDomainReference"),
        xml_id=xml_id(elem),
    )


def _parse_component_instance(elem: etree._Element) -> ComponentInstance:
    return ComponentInstance(
        instance_name=text(elem, "instanceName") or "",
        component_ref=parse_vlnv_ref(child(elem, "componentRef")),
        power_domain_links=parse_children(elem, "powerDomainLinks", "powerDomainLink", _parse_power_domain_link),
        **parse_name_group(elem),
        xml_id=xml_id(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_internal_port_reference(elem: etree._Element) -> InternalPortReference:
    return InternalPortReference(
        component_instance_ref=elem.get("componentInstanceRef", ""),
        port_ref=elem.get("portRef", ""),
        sub_port_refs=parse_sub_port_references(elem),
        part_select=parse_part_select(elem),
        xml_id=xml_id(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_external_port_reference(elem: etree._Element) -> ExternalPortReference:
    return ExternalPortReference(
        port_ref=elem.get("portRef", ""),
        sub_port_refs=parse_sub_port_references(elem),
        part_select=parse_part_select(elem),
        xml_id=xml_id(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_ad_hoc_connection(elem: etree._Element) -> AdHocConnection:
    return AdHocConnection(
        name=text(elem, "name") or "",
        internal_port_references=parse_children(
            elem, "portReferences", "internalPortReference", _parse_internal_port_reference
        ),
        external_port_references=parse_children(
            elem, "portReferences", "externalPortReference", _parse_external_port_reference
        ),
        tied_value=expr(elem, "tiedValue"),
        **parse_name_group(elem),
        xml_id=xml_id(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_active_interface(elem: etree._Element) -> ActiveInterface:
    return ActiveInterface(
        component_instance_ref=elem.get("componentInstanceRef", ""),
        bus_ref=elem.get("busRef", ""),
        exclude_ports=parse_children(elem, "excludePorts", "excludePort", text_value),
        description=text(elem, "description"),
        xml_id=xml_id(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_hier_interface(elem: etree._Element) -> HierInterface:
    return HierInterface(
        bus_ref=elem.get("busRef", ""),
        description=text(elem, "description"),
        xml_id=xml_id(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_interconnection(elem: etree._Element) -> Interconnection:
    active_interface_elems = children(elem, "activeInterface")
    active_interface = (
        _parse_active_interface(active_interface_elems[0])
        if active_interface_elems
        else ActiveInterface(component_instance_ref="", bus_ref="")
    )
    return Interconnection(
        name=text(elem, "name") or "",
        active_interface=active_interface,
        other_active_interfaces=[_parse_active_interface(e) for e in active_interface_elems[1:]],
        hier_interfaces=[_parse_hier_interface(e) for e in children(elem, "hierInterface")],
        **parse_name_group(elem),
        xml_id=xml_id(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_monitor_interface_ref(elem: etree._Element) -> MonitorInterfaceRef:
    return MonitorInterfaceRef(
        component_instance_ref=elem.get("componentInstanceRef", ""),
        bus_ref=elem.get("busRef", ""),
        path=elem.get("path"),
        description=text(elem, "description"),
        xml_id=xml_id(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_monitor_interconnection(elem: etree._Element) -> MonitorInterconnection:
    monitored_elem = child(elem, "monitoredActiveInterface")
    monitored_active_interface = (
        _parse_monitor_interface_ref(monitored_elem)
        if monitored_elem is not None
        else MonitorInterfaceRef(component_instance_ref="", bus_ref="")
    )
    return MonitorInterconnection(
        name=text(elem, "name") or "",
        monitored_active_interface=monitored_active_interface,
        monitor_interfaces=[_parse_monitor_interface_ref(e) for e in children(elem, "monitorInterface")],
        **parse_name_group(elem),
        xml_id=xml_id(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )
