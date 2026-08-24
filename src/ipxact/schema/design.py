from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .common import (
    Assertion,
    Choice,
    Expression,
    Parameter,
    PartSelect,
    SubPortReference,
    VendorExtension,
)
from .vlnv import VLNV, VLNVRef


@dataclass
class PowerDomainLink:
    """ipxact:powerDomainLink - links one external power domain to internal instance ones."""

    external_power_domain_ref: Expression
    internal_power_domain_refs: list[str] = field(default_factory=list)


@dataclass
class ComponentInstance:
    """ipxact:componentInstance - one instantiation of a component within this design."""

    instance_name: str
    component_ref: VLNVRef
    power_domain_links: list[PowerDomainLink] = field(default_factory=list)
    display_name: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class InternalPortReference:
    """ipxact:internalPortReference - a port on a component instance within this design."""

    component_instance_ref: str
    port_ref: str
    sub_port_refs: list[SubPortReference] = field(default_factory=list)
    part_select: Optional[PartSelect] = None
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class ExternalPortReference:
    """ipxact:externalPortReference - a port exposed by this design itself, one level up."""

    port_ref: str
    sub_port_refs: list[SubPortReference] = field(default_factory=list)
    part_select: Optional[PartSelect] = None
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class AdHocConnection:
    """ipxact:adHocConnection - a direct port-to-port connection outside any bus interface."""

    name: str
    internal_port_references: list[InternalPortReference] = field(default_factory=list)
    external_port_references: list[ExternalPortReference] = field(default_factory=list)
    tied_value: Optional[Expression] = None  # numeric expression, or "open"/"default"
    display_name: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class ActiveInterface:
    """ipxact:activeInterface - one endpoint of an interconnection: an instance's bus interface."""

    component_instance_ref: str
    bus_ref: str
    exclude_ports: list[str] = field(default_factory=list)
    description: Optional[str] = None
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class HierInterface:
    """ipxact:hierInterface - a bus interface exposed by this design itself, one level up."""

    bus_ref: str
    description: Optional[str] = None
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class Interconnection:
    """ipxact:interconnection - a bus connection between two or more active/hierarchical interfaces."""

    name: str
    active_interface: ActiveInterface
    other_active_interfaces: list[ActiveInterface] = field(default_factory=list)
    hier_interfaces: list[HierInterface] = field(default_factory=list)
    display_name: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class MonitorInterfaceRef:
    """A (component_instance, busInterface) pair referenced from a monitorInterconnection."""

    component_instance_ref: str
    bus_ref: str
    path: Optional[str] = None
    description: Optional[str] = None
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class MonitorInterconnection:
    """ipxact:monitorInterconnection - one active interface fanned out to any number of monitors."""

    name: str
    monitored_active_interface: MonitorInterfaceRef
    monitor_interfaces: list[MonitorInterfaceRef] = field(default_factory=list)
    display_name: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class Design:
    """ipxact:design - the root document for a hierarchical composition of component instances."""

    vlnv: VLNV
    component_instances: list[ComponentInstance] = field(default_factory=list)
    interconnections: list[Interconnection] = field(default_factory=list)
    monitor_interconnections: list[MonitorInterconnection] = field(default_factory=list)
    ad_hoc_connections: list[AdHocConnection] = field(default_factory=list)
    choices: list[Choice] = field(default_factory=list)
    parameters: list[Parameter] = field(default_factory=list)
    assertions: list[Assertion] = field(default_factory=list)
    display_name: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    vendor_extensions: list[VendorExtension] = field(default_factory=list)
