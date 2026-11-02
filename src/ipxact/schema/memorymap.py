from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Union

from .common import (
    AccessHandle,
    DefinitionRef,
    Expression,
    FieldReference,
    MemoryArray,
    ModeRef,
    Parameter,
    VendorExtension,
)


class AccessType(str, Enum):
    """ipxact:access enumeration (memoryMap.xsd accessType)."""

    READ_ONLY = "read-only"
    WRITE_ONLY = "write-only"
    READ_WRITE = "read-write"
    WRITE_ONCE = "writeOnce"
    READ_WRITE_ONCE = "read-writeOnce"
    NO_ACCESS = "no-access"


class UsageType(str, Enum):
    """ipxact:usage enumeration for an address block (memoryMap.xsd usageType)."""

    MEMORY = "memory"
    REGISTER = "register"
    RESERVED = "reserved"


class BankAlignment(str, Enum):
    """ipxact:bankAlignment attribute on a bank (memoryMap.xsd bankAlignmentType)."""

    SERIAL = "serial"
    PARALLEL = "parallel"


class SharedType(str, Enum):
    """ipxact:shared attribute on a memoryMap (memoryMap.xsd sharedType)."""

    YES = "yes"
    NO = "no"
    UNDEFINED = "undefined"


class ModifiedWriteValue(str, Enum):
    """ipxact:modifiedWriteValue enumeration (memoryMap.xsd modifiedWriteValueType)."""

    ONE_TO_CLEAR = "oneToClear"
    ONE_TO_SET = "oneToSet"
    ONE_TO_TOGGLE = "oneToToggle"
    ZERO_TO_CLEAR = "zeroToClear"
    ZERO_TO_SET = "zeroToSet"
    ZERO_TO_TOGGLE = "zeroToToggle"
    CLEAR = "clear"
    SET = "set"
    MODIFY = "modify"


class ReadAction(str, Enum):
    """ipxact:readAction enumeration (memoryMap.xsd readActionType)."""

    CLEAR = "clear"
    SET = "set"
    MODIFY = "modify"


class TestConstraint(str, Enum):
    """ipxact:testable/@testConstraint enumeration (memoryMap.xsd)."""

    UNCONSTRAINED = "unconstrained"
    RESTORE = "restore"
    WRITE_AS_READ = "writeAsRead"
    READ_ONLY = "readOnly"


@dataclass
class Reset:
    """ipxact:reset - a bit field's reset value under a given reset signal."""

    value: Expression
    mask: Optional[Expression] = None
    reset_type_ref: Optional[str] = None
    xml_id: Optional[str] = None


@dataclass
class EnumeratedValue:
    """ipxact:enumeratedValue - one named legal value of a bit field."""

    name: str
    value: Expression
    usage: str = "read-write"  # read/write/read-write
    display_name: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    xml_id: Optional[str] = None
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class WriteValueConstraint:
    """ipxact:writeValueConstraint - the legal values that may be written to a field."""

    write_as_read: Optional[bool] = None
    use_enumerated_values: Optional[bool] = None
    minimum: Optional[Expression] = None
    maximum: Optional[Expression] = None


@dataclass
class AccessRestriction:
    """ipxact:accessRestriction - a read/write bitmask that applies for one or more modes."""

    mode_refs: list[ModeRef] = field(default_factory=list)
    read_access_mask: Optional[Expression] = None
    write_access_mask: Optional[Expression] = None
    xml_id: Optional[str] = None


@dataclass
class AccessPolicy:
    """ipxact:accessPolicy - the access allowed for a register/block/bank, for one or more modes."""

    mode_refs: list[ModeRef] = field(default_factory=list)
    access: Optional[AccessType] = None
    xml_id: Optional[str] = None
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class FieldAccessPolicy:
    """ipxact:fieldAccessPolicy - a field's read/write behavior, for one or more modes.

    ``modified_write_value_modify`` / ``read_action_modify`` hold the ``modify`` attribute, which
    names the user-defined behavior when the value is "modify".
    """

    mode_refs: list[ModeRef] = field(default_factory=list)
    field_access_policy_definition_ref: Optional[DefinitionRef] = None
    access: Optional[AccessType] = None
    modified_write_value: Optional[ModifiedWriteValue] = None
    modified_write_value_modify: Optional[str] = None
    write_value_constraint: Optional[WriteValueConstraint] = None
    read_action: Optional[ReadAction] = None
    read_action_modify: Optional[str] = None
    read_response: Optional[Expression] = None
    broadcast_to: list[FieldReference] = field(default_factory=list)
    access_restrictions: list[AccessRestriction] = field(default_factory=list)
    testable: Optional[bool] = None
    test_constraint: Optional[TestConstraint] = None
    reserved: Optional[Expression] = None
    xml_id: Optional[str] = None
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class Field:
    """ipxact:field - a bit field within a register (memoryMap.xsd fieldType).

    A field either describes itself inline (bit_width, volatile, resets, ...), points to a
    typeDefinitions field definition (``field_definition_ref``), or is an alias of another field
    (``alias_of``). ``enumeration_definition_ref`` replaces ``enumerated_values`` the same way.
    """

    name: str
    bit_offset: Expression
    bit_width: Optional[Expression] = None
    access_handles: list[AccessHandle] = field(default_factory=list)
    array: Optional[MemoryArray] = None
    field_definition_ref: Optional[DefinitionRef] = None
    type_identifier: Optional[str] = None
    volatile: Optional[bool] = None
    resets: list[Reset] = field(default_factory=list)
    alias_of: Optional[FieldReference] = None
    field_access_policies: list[FieldAccessPolicy] = field(default_factory=list)
    field_access_policies_xml_id: Optional[str] = None
    enumerated_values: list[EnumeratedValue] = field(default_factory=list)
    enumeration_definition_ref: Optional[DefinitionRef] = None
    display_name: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    parameters: list[Parameter] = field(default_factory=list)
    xml_id: Optional[str] = None
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class AlternateRegister:
    """ipxact:alternateRegister - an alternate field layout for a register, selected by mode."""

    name: str
    access_handles: list[AccessHandle] = field(default_factory=list)
    mode_refs: list[ModeRef] = field(default_factory=list)
    type_identifier: Optional[str] = None
    volatile: Optional[bool] = None
    access_policies: list[AccessPolicy] = field(default_factory=list)
    fields: list[Field] = field(default_factory=list)
    display_name: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    parameters: list[Parameter] = field(default_factory=list)
    xml_id: Optional[str] = None
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class Register:
    """ipxact:register - a named, addressed register made of fields.

    ``register_definition_ref`` replaces the inline content (size, fields, ...) when set.
    """

    name: str
    address_offset: Expression
    size: Optional[Expression] = None
    access_handles: list[AccessHandle] = field(default_factory=list)
    array: Optional[MemoryArray] = None
    register_definition_ref: Optional[DefinitionRef] = None
    type_identifier: Optional[str] = None
    volatile: Optional[bool] = None
    access_policies: list[AccessPolicy] = field(default_factory=list)
    fields: list[Field] = field(default_factory=list)
    alternate_registers: list[AlternateRegister] = field(default_factory=list)
    display_name: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    parameters: list[Parameter] = field(default_factory=list)
    xml_id: Optional[str] = None
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class RegisterFile:
    """ipxact:registerFile - a nested structure of registers and register files.

    ``register_file_definition_ref`` replaces the inline content (range, registers, ...) when set.
    """

    name: str
    address_offset: Expression
    range: Optional[Expression] = None
    access_handles: list[AccessHandle] = field(default_factory=list)
    array: Optional[MemoryArray] = None
    register_file_definition_ref: Optional[DefinitionRef] = None
    type_identifier: Optional[str] = None
    access_policies: list[AccessPolicy] = field(default_factory=list)
    registers: list[Union[Register, "RegisterFile"]] = field(default_factory=list)
    display_name: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    parameters: list[Parameter] = field(default_factory=list)
    xml_id: Optional[str] = None
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class AddressBlock:
    """ipxact:addressBlock - a contiguous, addressed block of registers.

    base_address is unset when the block sits inside a Bank: banked blocks do not carry
    their own address, matching the schema's separate (address-less) bankedBlockType.
    ``address_block_definition_ref`` replaces the inline content (range, width, registers, ...)
    when set.
    """

    name: str
    range: Optional[Expression] = None
    width: Optional[Expression] = None
    base_address: Optional[Expression] = None
    access_handles: list[AccessHandle] = field(default_factory=list)
    array: Optional[MemoryArray] = None
    address_block_definition_ref: Optional[DefinitionRef] = None
    type_identifier: Optional[str] = None
    usage: Optional[UsageType] = None
    volatile: Optional[bool] = None
    access_policies: list[AccessPolicy] = field(default_factory=list)
    registers: list[Union[Register, RegisterFile]] = field(default_factory=list)
    misalignment_allowed: bool = True
    display_name: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    parameters: list[Parameter] = field(default_factory=list)
    xml_id: Optional[str] = None
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class SubspaceMap:
    """ipxact:subspaceMap - maps in an address subspace from across a bus bridge.

    base_address is unset when the map sits inside a Bank, for the same reason as
    AddressBlock.base_address.
    """

    name: str
    initiator_ref: str
    base_address: Optional[Expression] = None
    segment_ref: Optional[str] = None
    display_name: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    parameters: list[Parameter] = field(default_factory=list)
    xml_id: Optional[str] = None
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


MemoryMapItem = Union["Bank", AddressBlock, SubspaceMap]


@dataclass
class Bank:
    """ipxact:bank - a bank of address blocks or nested banks, aligned serially or in parallel.

    base_address is unset when this bank is nested inside another bank: nested banks do not
    carry their own address, matching the schema's separate (address-less) bankedBankType.
    ``bank_definition_ref`` replaces the inline content (items, usage, ...) when set.
    """

    name: str
    bank_alignment: BankAlignment
    base_address: Optional[Expression] = None
    access_handles: list[AccessHandle] = field(default_factory=list)
    bank_definition_ref: Optional[DefinitionRef] = None
    items: list[MemoryMapItem] = field(default_factory=list)
    usage: Optional[UsageType] = None
    volatile: Optional[bool] = None
    access_policies: list[AccessPolicy] = field(default_factory=list)
    parameters: list[Parameter] = field(default_factory=list)
    display_name: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    xml_id: Optional[str] = None
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class MemoryRemap:
    """ipxact:memoryRemap - additional memoryMap content that only applies in given modes.

    ``remap_definition_ref`` replaces the inline items when set.
    """

    name: str
    mode_refs: list[ModeRef] = field(default_factory=list)
    remap_definition_ref: Optional[DefinitionRef] = None
    items: list[MemoryMapItem] = field(default_factory=list)
    display_name: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    xml_id: Optional[str] = None
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class MemoryMap:
    """ipxact:memoryMap - a component's addressable space, made of address blocks/banks/subspace maps.

    ``memory_map_definition_ref`` replaces the inline content (items, remaps, ...) when set.
    """

    name: str
    memory_map_definition_ref: Optional[DefinitionRef] = None
    items: list[MemoryMapItem] = field(default_factory=list)
    memory_remaps: list[MemoryRemap] = field(default_factory=list)
    address_unit_bits: Optional[Expression] = None
    shared: Optional[SharedType] = None
    display_name: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    xml_id: Optional[str] = None
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class LocalMemoryMap:
    """ipxact:localMemoryMap - the memory map local to one address space (accessible only via it)."""

    name: str
    items: list[Union[Bank, AddressBlock]] = field(default_factory=list)
    display_name: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    xml_id: Optional[str] = None
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class Segment:
    """ipxact:segment - a named sub-range of an address space."""

    name: str
    address_offset: Expression
    range: Expression
    display_name: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    xml_id: Optional[str] = None
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class AddressSpace:
    """ipxact:addressSpace - a logical address space exposed by an initiator bus interface."""

    name: str
    range: Expression
    width: Expression
    segments: list[Segment] = field(default_factory=list)
    address_unit_bits: Optional[Expression] = None
    local_memory_map: Optional[LocalMemoryMap] = None
    display_name: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    parameters: list[Parameter] = field(default_factory=list)
    xml_id: Optional[str] = None
    vendor_extensions: list[VendorExtension] = field(default_factory=list)
