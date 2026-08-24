from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .common import Assertion, Choice, Parameter, VendorExtension
from .vlnv import VLNV, VLNVRef


@dataclass
class InterfaceRef:
    """ipxact:interfaceRef - one broadcast endpoint an abstractor chain applies to."""

    component_ref: str
    bus_ref: str
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class AbstractorInstance:
    """ipxact:abstractorInstance - one abstractor in a chain, with its active view."""

    instance_name: str
    abstractor_ref: VLNVRef
    view_name: str
    display_name: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None


@dataclass
class AbstractorChain:
    """ipxact:abstractorInstances - a chain of abstractors bridging one interconnection endpoint."""

    abstractors: list[AbstractorInstance] = field(default_factory=list)
    interface_refs: list[InterfaceRef] = field(default_factory=list)
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class InterconnectionConfiguration:
    """ipxact:interconnectionConfiguration - the abstractors needed to bridge one interconnection."""

    interconnection_ref: str
    abstractor_chains: list[AbstractorChain] = field(default_factory=list)
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class ViewConfiguration:
    """ipxact:viewConfiguration - the active view (and its parameter values) for one component instance."""

    instance_name: str
    view_ref: str
    configurable_element_values: dict[str, str] = field(default_factory=dict)
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class DesignConfiguration:
    """ipxact:designConfiguration - the current configuration of a design (views, abstractors), not instance parameterization."""

    vlnv: VLNV
    design_ref: Optional[VLNVRef] = None
    generator_chain_configurations: list[VLNVRef] = field(default_factory=list)
    interconnection_configurations: list[InterconnectionConfiguration] = field(default_factory=list)
    view_configurations: list[ViewConfiguration] = field(default_factory=list)
    choices: list[Choice] = field(default_factory=list)
    parameters: list[Parameter] = field(default_factory=list)
    assertions: list[Assertion] = field(default_factory=list)
    display_name: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    vendor_extensions: list[VendorExtension] = field(default_factory=list)
