from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .businterface import FieldReference
from .common import Expression, Parameter, PartSelect, SubPortReference, VendorExtension
from .vlnv import VLNVRef


@dataclass
class ExternalTypeDefinitionsRef:
    """ipxact:typeDefinitions/externalTypeDefinitions - a reference to a shared typeDefinitions document.

    The typeDefinitions document type itself (and the *DefinitionRef indirection it enables
    on address blocks/registers/fields/banks/memory maps) is out of scope for v1; see
    memorymap.py and businterface.py, which model the fully-resolved inline shape only.
    """

    type_definitions: VLNVRef
    name: Optional[str] = None


@dataclass
class PowerDomain:
    """ipxact:powerDomain - a named power domain defined on this component."""

    name: str
    always_on: Optional[Expression] = None
    sub_domain_of: Optional[str] = None
    parameters: list[Parameter] = field(default_factory=list)
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class CpuRegion:
    """ipxact:region - an address region within a cpu's system address map."""

    name: str
    address_offset: Expression
    range: Expression
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class Cpu:
    """ipxact:cpu - a processor instance in this component.

    ``executableImage`` (boot-image / software-loading metadata) is out of scope: it
    describes software payloads, not hardware structure.
    """

    name: str
    range: Expression
    width: Expression
    memory_map_ref: str
    regions: list[CpuRegion] = field(default_factory=list)
    address_unit_bits: Optional[Expression] = None
    parameters: list[Parameter] = field(default_factory=list)
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class PortSlice:
    """ipxact:portSlice - a named reference to a port (or part of one), used within a mode."""

    name: str
    port_ref: str
    sub_port_refs: list[SubPortReference] = field(default_factory=list)
    part_select: Optional[PartSelect] = None
    display_name: Optional[str] = None
    description: Optional[str] = None


@dataclass
class FieldSlice:
    """ipxact:fieldSlice - a named reference to a register field, used within a mode."""

    name: str
    field_ref: FieldReference
    display_name: Optional[str] = None
    description: Optional[str] = None


@dataclass
class Mode:
    """ipxact:mode - a user-defined operating mode, selecting port/field slices and a condition."""

    name: str
    port_slices: list[PortSlice] = field(default_factory=list)
    field_slices: list[FieldSlice] = field(default_factory=list)
    condition: Optional[Expression] = None
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class ClearboxElement:
    """ipxact:clearboxElement - an internal signal/pin/interface exposed for whitebox access."""

    name: str
    clearbox_type: str  # signal/pin/interface
    driveable: bool = False
    parameters: list[Parameter] = field(default_factory=list)
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class ComponentGenerator:
    """ipxact:componentGenerator - an external generator tool invocable on this component."""

    name: str
    generator_exe: str
    phase: Optional[Expression] = None
    parameters: list[Parameter] = field(default_factory=list)
    api_type: Optional[str] = None
    api_service: str = "SOAP"
    transport_methods: list[str] = field(default_factory=list)
    groups: list[str] = field(default_factory=list)
    scope: str = "instance"  # instance/entity
    hidden: bool = False
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class ResetType:
    """ipxact:resetType - a user-defined reset policy applicable to this component."""

    name: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class OtherClockDriver:
    """ipxact:otherClockDriver - a clock not directly associated with an input port."""

    clock_name: str
    clock_period: Expression
    clock_pulse_offset: Expression
    clock_pulse_value: Expression
    clock_pulse_duration: Expression
    clock_source: Optional[str] = None
    period_units: str = "ns"
    offset_units: str = "ns"
    duration_units: str = "ns"
