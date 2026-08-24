from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .businterface import BusInterface, Channel, IndirectInterface
from .common import Assertion, Choice, FileSet, Parameter, VendorExtension
from .component_sections import (
    ClearboxElement,
    ComponentGenerator,
    Cpu,
    ExternalTypeDefinitionsRef,
    Mode,
    OtherClockDriver,
    PowerDomain,
    ResetType,
)
from .memorymap import AddressSpace, MemoryMap
from .model import Model
from .vlnv import VLNV


@dataclass
class Component:
    """ipxact:component - the root document for a reusable IP (component.xsd componentType).

    A complete mapping of componentType, with the following deliberate simplifications
    (see the design discussion this session): no xml:id (XML-internal plumbing, no domain
    meaning), vendorExtensions kept as opaque raw XML rather than modeled, and no
    definition/instance indirection (a component always presents its fully-inline shape;
    resolving a typeDefinitions reference into that shape is the parser's job, not the
    object model's). A handful of SystemC/TLM/PSS-only leaf features are also out of scope;
    see the docstrings in ports.py, memorymap.py and component_sections.py for each one.
    """

    vlnv: VLNV
    bus_interfaces: list[BusInterface] = field(default_factory=list)
    indirect_interfaces: list[IndirectInterface] = field(default_factory=list)
    channels: list[Channel] = field(default_factory=list)
    modes: list[Mode] = field(default_factory=list)
    address_spaces: list[AddressSpace] = field(default_factory=list)
    memory_maps: list[MemoryMap] = field(default_factory=list)
    model: Optional[Model] = None
    component_generators: list[ComponentGenerator] = field(default_factory=list)
    choices: list[Choice] = field(default_factory=list)
    file_sets: list[FileSet] = field(default_factory=list)
    clearbox_elements: list[ClearboxElement] = field(default_factory=list)
    cpus: list[Cpu] = field(default_factory=list)
    other_clock_drivers: list[OtherClockDriver] = field(default_factory=list)
    reset_types: list[ResetType] = field(default_factory=list)
    power_domains: list[PowerDomain] = field(default_factory=list)
    external_type_definitions: list[ExternalTypeDefinitionsRef] = field(default_factory=list)
    parameters: list[Parameter] = field(default_factory=list)
    assertions: list[Assertion] = field(default_factory=list)
    display_name: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    vendor_extensions: list[VendorExtension] = field(default_factory=list)
