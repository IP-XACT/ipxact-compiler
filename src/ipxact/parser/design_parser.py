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
    parse_assertions,
    parse_choices,
    parse_parameters,
    parse_part_select,
    parse_sub_port_references,
    parse_vendor_extensions,
    parse_vlnv,
    parse_vlnv_ref,
    qn,
    text,
    texts,
)


def parse_design(root: etree._Element) -> Design:
    """Parse an ipxact:design root element into a Design object."""
    component_instances_container = child(root, "componentInstances")
    interconnections_container = child(root, "interconnections")
    ad_hoc_connections_container = child(root, "adHocConnections")

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
        component_instances=(
            [_parse_component_instance(e) for e in children(component_instances_container, "componentInstance")]
            if component_instances_container is not None
            else []
        ),
        interconnections=interconnections,
        monitor_interconnections=monitor_interconnections,
        ad_hoc_connections=(
            [_parse_ad_hoc_connection(e) for e in children(ad_hoc_connections_container, "adHocConnection")]
            if ad_hoc_connections_container is not None
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


def _parse_power_domain_link(elem: etree._Element) -> PowerDomainLink:
    return PowerDomainLink(
        external_power_domain_ref=text(elem, "externalPowerDomainReference") or "",
        internal_power_domain_refs=texts(elem, "internalPowerDomainReference"),
    )


def _parse_component_instance(elem: etree._Element) -> ComponentInstance:
    power_domain_links_container = child(elem, "powerDomainLinks")
    return ComponentInstance(
        instance_name=text(elem, "instanceName") or "",
        component_ref=parse_vlnv_ref(child(elem, "componentRef")),
        power_domain_links=(
            [_parse_power_domain_link(e) for e in children(power_domain_links_container, "powerDomainLink")]
            if power_domain_links_container is not None
            else []
        ),
        display_name=text(elem, "displayName"),
        short_description=text(elem, "shortDescription"),
        description=text(elem, "description"),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_internal_port_reference(elem: etree._Element) -> InternalPortReference:
    return InternalPortReference(
        component_instance_ref=elem.get("componentInstanceRef", ""),
        port_ref=elem.get("portRef", ""),
        sub_port_refs=parse_sub_port_references(elem),
        part_select=parse_part_select(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_external_port_reference(elem: etree._Element) -> ExternalPortReference:
    return ExternalPortReference(
        port_ref=elem.get("portRef", ""),
        sub_port_refs=parse_sub_port_references(elem),
        part_select=parse_part_select(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_ad_hoc_connection(elem: etree._Element) -> AdHocConnection:
    references_container = child(elem, "portReferences")
    internal_refs: list[InternalPortReference] = []
    external_refs: list[ExternalPortReference] = []
    if references_container is not None:
        internal_refs = [
            _parse_internal_port_reference(e) for e in children(references_container, "internalPortReference")
        ]
        external_refs = [
            _parse_external_port_reference(e) for e in children(references_container, "externalPortReference")
        ]
    return AdHocConnection(
        name=text(elem, "name") or "",
        internal_port_references=internal_refs,
        external_port_references=external_refs,
        tied_value=text(elem, "tiedValue"),
        display_name=text(elem, "displayName"),
        short_description=text(elem, "shortDescription"),
        description=text(elem, "description"),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_active_interface(elem: etree._Element) -> ActiveInterface:
    exclude_ports_container = child(elem, "excludePorts")
    return ActiveInterface(
        component_instance_ref=elem.get("componentInstanceRef", ""),
        bus_ref=elem.get("busRef", ""),
        exclude_ports=(
            texts(exclude_ports_container, "excludePort") if exclude_ports_container is not None else []
        ),
        description=text(elem, "description"),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_hier_interface(elem: etree._Element) -> HierInterface:
    return HierInterface(
        bus_ref=elem.get("busRef", ""),
        description=text(elem, "description"),
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
        display_name=text(elem, "displayName"),
        short_description=text(elem, "shortDescription"),
        description=text(elem, "description"),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_monitor_interface_ref(elem: etree._Element) -> MonitorInterfaceRef:
    return MonitorInterfaceRef(
        component_instance_ref=elem.get("componentInstanceRef", ""),
        bus_ref=elem.get("busRef", ""),
        path=elem.get("path"),
        description=text(elem, "description"),
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
        display_name=text(elem, "displayName"),
        short_description=text(elem, "shortDescription"),
        description=text(elem, "description"),
        vendor_extensions=parse_vendor_extensions(elem),
    )
