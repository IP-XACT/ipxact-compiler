from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from .common import Expression, ModeRef, Parameter, PartSelect, VendorExtension
from .vlnv import VLNVRef


class InterfaceMode(str, Enum):
    """ipxact:interfaceMode group - the role a busInterface plays (model.xsd interfaceMode)."""

    INITIATOR = "initiator"
    TARGET = "target"
    SYSTEM = "system"
    MIRRORED_INITIATOR = "mirroredInitiator"
    MIRRORED_TARGET = "mirroredTarget"
    MIRRORED_SYSTEM = "mirroredSystem"
    MONITOR = "monitor"


@dataclass
class PortMap:
    """ipxact:portMap - maps a bus definition logical port to a component physical port."""

    logical_port: str
    physical_port: Optional[str] = None
    logical_tie_off: Optional[Expression] = None
    invert: bool = False
    is_informative: bool = False


@dataclass
class AbstractionType:
    """ipxact:abstractionType - one abstraction level (e.g. RTL) of a busInterface."""

    abstraction_ref: VLNVRef
    port_maps: list[PortMap] = field(default_factory=list)
    view_refs: list[str] = field(default_factory=list)


@dataclass
class TransparentBridge:
    """ipxact:transparentBridge - a target interface bridging transparently to an initiator interface."""

    initiator_ref: str


@dataclass
class InitiatorInterface:
    """ipxact:initiator - role-specific content of a busInterface acting as initiator."""

    address_space_ref: Optional[str] = None
    base_address: Optional[Expression] = None
    mode_refs: list[ModeRef] = field(default_factory=list)


@dataclass
class FileSetRefGroup:
    """ipxact:fileSetRefGroup - fileSets associated with one function of a target interface."""

    group: Optional[str] = None
    file_set_refs: list[str] = field(default_factory=list)


@dataclass
class TargetInterface:
    """ipxact:target - role-specific content of a busInterface acting as target."""

    memory_map_ref: Optional[str] = None
    mode_refs: list[ModeRef] = field(default_factory=list)
    transparent_bridges: list[TransparentBridge] = field(default_factory=list)
    file_set_ref_groups: list[FileSetRefGroup] = field(default_factory=list)


@dataclass
class RemapAddress:
    """ipxact:remapAddress - one mode-selected base address of a mirroredTarget interface."""

    value: Expression
    mode_refs: list[ModeRef] = field(default_factory=list)


@dataclass
class MirroredTargetInterface:
    """ipxact:mirroredTarget - role-specific content of a busInterface acting as mirrored target."""

    remap_addresses: list[RemapAddress] = field(default_factory=list)
    range: Optional[Expression] = None


@dataclass
class SystemInterface:
    """ipxact:system / ipxact:mirroredSystem - which system group this interface belongs to."""

    group: str


@dataclass
class MonitorInterface:
    """ipxact:monitor - a passive monitor of another interface mode on this component."""

    interface_mode: InterfaceMode
    group: Optional[str] = None


@dataclass
class BusInterface:
    """ipxact:busInterface - a protocol-typed logical grouping of ports (busInterface.xsd).

    Exactly one of initiator/target/system/mirrored_target/mirrored_system/monitor is set,
    matching ``mode`` (mirroredInitiator carries no extra content beyond the mode itself).
    """

    name: str
    bus_type: VLNVRef
    mode: InterfaceMode
    abstraction_types: list[AbstractionType] = field(default_factory=list)
    initiator: Optional[InitiatorInterface] = None
    target: Optional[TargetInterface] = None
    system: Optional[SystemInterface] = None
    mirrored_target: Optional[MirroredTargetInterface] = None
    mirrored_system: Optional[SystemInterface] = None
    monitor: Optional[MonitorInterface] = None
    connection_required: bool = False
    bits_in_lau: Optional[Expression] = None
    bit_steering: Optional[Expression] = None
    endianness: Optional[str] = None
    parameters: list[Parameter] = field(default_factory=list)
    display_name: Optional[str] = None
    description: Optional[str] = None
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class FieldReference:
    """A pointer into the memory-map hierarchy down to one field.

    Covers both commonStructures.fieldReferenceGroup (used by indirectAddressRef/
    indirectDataRef and a field's aliasOf, where addressBlockRef/registerRef are optional)
    and fieldSliceReferenceGroup (used by mode/fieldSlice, where they are required and a
    trailing bit range is allowed). Python fields are left optional in both cases; nothing
    at this layer enforces which combination the source element actually requires.
    """

    field_ref: str
    register_ref: Optional[str] = None
    alternate_register_ref: Optional[str] = None
    register_file_refs: list[str] = field(default_factory=list)
    address_block_ref: Optional[str] = None
    bank_refs: list[str] = field(default_factory=list)
    memory_map_ref: Optional[str] = None
    memory_remap_ref: Optional[str] = None
    address_space_ref: Optional[str] = None
    range: Optional[PartSelect] = None


@dataclass
class IndirectInterface:
    """ipxact:indirectInterface - a memory map accessed indirectly through address/data fields."""

    name: str
    indirect_address_ref: FieldReference
    indirect_data_ref: FieldReference
    memory_map_ref: Optional[str] = None
    transparent_bridges: list[TransparentBridge] = field(default_factory=list)
    bits_in_lau: Optional[Expression] = None
    endianness: Optional[str] = None
    display_name: Optional[str] = None
    description: Optional[str] = None
    parameters: list[Parameter] = field(default_factory=list)
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class Channel:
    """ipxact:channel - a set of mirrored bus interfaces of this component connected to one another."""

    name: str
    bus_interface_refs: list[str] = field(default_factory=list)
    display_name: Optional[str] = None
    description: Optional[str] = None
    vendor_extensions: list[VendorExtension] = field(default_factory=list)
