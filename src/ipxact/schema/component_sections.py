from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .common import (
    Expression,
    FieldReference,
    FileBuilder,
    FileSetRefGroup,
    Parameter,
    PartSelect,
    SubPortReference,
    TextValue,
    VendorExtension,
)
from .vlnv import VLNVRef


@dataclass
class ViewLink:
    """ipxact:viewLink - maps a view of the referenced typeDefinitions document to a view of this component."""

    external_view_ref: str
    view_ref: str
    xml_id: Optional[str] = None
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class ModeLink:
    """ipxact:modeLink - maps a mode of the referenced typeDefinitions document to a mode of this component."""

    external_mode_ref: str
    mode_ref: str
    xml_id: Optional[str] = None
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class ResetTypeLink:
    """ipxact:resetTypeLink - maps a reset type of the referenced typeDefinitions document to one of
    this component."""

    external_reset_type_ref: str
    reset_type_ref: str
    xml_id: Optional[str] = None
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class ExternalTypeDefinitionsRef:
    """ipxact:typeDefinitions/externalTypeDefinitions - a reference to a shared typeDefinitions document.

    The ``*DefinitionRef`` elements of memory maps, banks, address blocks, register files,
    registers, fields, ... point into it by this element's ``name``. The typeDefinitions
    document itself is not parsed by this library.
    """

    type_definitions: VLNVRef
    name: Optional[str] = None
    view_links: list[ViewLink] = field(default_factory=list)
    mode_links: list[ModeLink] = field(default_factory=list)
    reset_type_links: list[ResetTypeLink] = field(default_factory=list)
    display_name: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    xml_id: Optional[str] = None
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class PowerDomain:
    """ipxact:powerDomain - a named power domain defined on this component."""

    name: str
    always_on: Optional[Expression] = None
    sub_domain_of: Optional[str] = None
    parameters: list[Parameter] = field(default_factory=list)
    display_name: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    xml_id: Optional[str] = None
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class CpuRegion:
    """ipxact:region - an address region within a cpu's system address map."""

    name: str
    address_offset: Expression
    range: Expression
    display_name: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    xml_id: Optional[str] = None
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class LinkerCommandFile:
    """ipxact:linkerCommandFile - a linker command file used to build an executable image."""

    name: Expression
    command_line_switch: Expression
    enable: Expression
    generator_refs: list[TextValue] = field(default_factory=list)
    xml_id: Optional[str] = None
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class LanguageTools:
    """ipxact:languageTools - the compilers and linker used to build an executable image."""

    file_builders: list[FileBuilder] = field(default_factory=list)
    linker: Optional[Expression] = None
    linker_flags: Optional[Expression] = None
    linker_command_file: Optional[LinkerCommandFile] = None


@dataclass
class ExecutableImage:
    """ipxact:executableImage - a software image (and how to build it) that runs on a cpu."""

    name: str
    image_id: str
    image_type: Optional[str] = None
    parameters: list[Parameter] = field(default_factory=list)
    language_tools: Optional[LanguageTools] = None
    file_set_ref_group: Optional[FileSetRefGroup] = None
    display_name: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    xml_id: Optional[str] = None
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class Cpu:
    """ipxact:cpu - a processor instance in this component."""

    name: str
    range: Expression
    width: Expression
    memory_map_ref: str
    regions: list[CpuRegion] = field(default_factory=list)
    address_unit_bits: Optional[Expression] = None
    executable_images: list[ExecutableImage] = field(default_factory=list)
    parameters: list[Parameter] = field(default_factory=list)
    display_name: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    xml_id: Optional[str] = None
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class PortSlice:
    """ipxact:portSlice - a named reference to a port (or part of one), used within a mode."""

    name: str
    port_ref: str
    sub_port_refs: list[SubPortReference] = field(default_factory=list)
    part_select: Optional[PartSelect] = None
    display_name: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    xml_id: Optional[str] = None


@dataclass
class FieldSlice:
    """ipxact:fieldSlice - a named reference to a register field, used within a mode."""

    name: str
    field_ref: FieldReference
    display_name: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    xml_id: Optional[str] = None


@dataclass
class Mode:
    """ipxact:mode - a user-defined operating mode, selecting port/field slices and a condition."""

    name: str
    port_slices: list[PortSlice] = field(default_factory=list)
    field_slices: list[FieldSlice] = field(default_factory=list)
    condition: Optional[Expression] = None
    display_name: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    xml_id: Optional[str] = None
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class ClearboxElement:
    """ipxact:clearboxElement - an internal signal/pin/interface exposed for whitebox access."""

    name: str
    clearbox_type: str  # signal/pin/interface
    driveable: bool = False
    parameters: list[Parameter] = field(default_factory=list)
    display_name: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    xml_id: Optional[str] = None
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class ComponentGenerator:
    """ipxact:componentGenerator - an external generator tool invocable on this component."""

    name: str
    generator_exe: str
    phase: Optional[Expression] = None
    parameters: list[Parameter] = field(default_factory=list)
    api_type: Optional[TextValue] = None
    api_service: str = "SOAP"
    transport_methods: list[TextValue] = field(default_factory=list)
    transport_methods_xml_id: Optional[str] = None
    groups: list[TextValue] = field(default_factory=list)
    scope: str = "instance"  # instance/entity
    hidden: bool = False
    display_name: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    xml_id: Optional[str] = None
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class ResetType:
    """ipxact:resetType - a user-defined reset policy applicable to this component."""

    name: str
    display_name: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    xml_id: Optional[str] = None
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
    xml_id: Optional[str] = None
