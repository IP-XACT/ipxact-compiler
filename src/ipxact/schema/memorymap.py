from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Union

from .common import Expression, MemoryArray, ModeRef, Parameter, VendorExtension


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


@dataclass
class EnumeratedValue:
    """ipxact:enumeratedValue - one named legal value of a bit field."""

    name: str
    value: Expression
    usage: str = "read-write"  # read/write/read-write
    display_name: Optional[str] = None
    description: Optional[str] = None


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


@dataclass
class AccessPolicy:
    """ipxact:accessPolicy - the access allowed for a register/block/bank, for one or more modes."""

    mode_refs: list[ModeRef] = field(default_factory=list)
    access: Optional[AccessType] = None


@dataclass
class FieldAccessPolicy:
    """ipxact:fieldAccessPolicy - a field's read/write behavior, for one or more modes."""

    mode_refs: list[ModeRef] = field(default_factory=list)
    access: Optional[AccessType] = None
    modified_write_value: Optional[ModifiedWriteValue] = None
    write_value_constraint: Optional[WriteValueConstraint] = None
    read_action: Optional[ReadAction] = None
    read_response: Optional[Expression] = None
    broadcast_to: list[str] = field(default_factory=list)
    access_restrictions: list[AccessRestriction] = field(default_factory=list)
    testable: Optional[bool] = None
    test_constraint: Optional[TestConstraint] = None
    reserved: Optional[Expression] = None


@dataclass
class Field:
    """ipxact:field - a bit field within a register (memoryMap.xsd fieldType).

    fieldType's ``aliasOf`` alternative (a field that is purely an alias reference to
    another field, in place of its own bit_offset/bit_width/access data) is out of scope.
    """

    name: str
    bit_offset: Expression
    bit_width: Expression
    array: Optional[MemoryArray] = None
    volatile: Optional[bool] = None
    resets: list[Reset] = field(default_factory=list)
    field_access_policies: list[FieldAccessPolicy] = field(default_factory=list)
    enumerated_values: list[EnumeratedValue] = field(default_factory=list)
    display_name: Optional[str] = None
    description: Optional[str] = None
    parameters: list[Parameter] = field(default_factory=list)
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class AlternateRegister:
    """ipxact:alternateRegister - an alternate field layout for a register, selected by mode."""

    name: str
    mode_refs: list[ModeRef] = field(default_factory=list)
    volatile: Optional[bool] = None
    access_policies: list[AccessPolicy] = field(default_factory=list)
    fields: list[Field] = field(default_factory=list)
    display_name: Optional[str] = None
    description: Optional[str] = None
    parameters: list[Parameter] = field(default_factory=list)
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class Register:
    """ipxact:register - a named, addressed register made of fields."""

    name: str
    address_offset: Expression
    size: Expression
    array: Optional[MemoryArray] = None
    volatile: Optional[bool] = None
    access_policies: list[AccessPolicy] = field(default_factory=list)
    fields: list[Field] = field(default_factory=list)
    alternate_registers: list[AlternateRegister] = field(default_factory=list)
    display_name: Optional[str] = None
    description: Optional[str] = None
    parameters: list[Parameter] = field(default_factory=list)
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class RegisterFile:
    """ipxact:registerFile - a nested structure of registers and register files."""

    name: str
    address_offset: Expression
    range: Expression
    array: Optional[MemoryArray] = None
    access_policies: list[AccessPolicy] = field(default_factory=list)
    registers: list[Union[Register, "RegisterFile"]] = field(default_factory=list)
    display_name: Optional[str] = None
    description: Optional[str] = None
    parameters: list[Parameter] = field(default_factory=list)
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class AddressBlock:
    """ipxact:addressBlock - a contiguous, addressed block of registers.

    base_address is unset when the block sits inside a Bank: banked blocks do not carry
    their own address, matching the schema's separate (address-less) bankedBlockType.
    """

    name: str
    range: Expression
    width: Expression
    base_address: Optional[Expression] = None
    usage: Optional[UsageType] = None
    volatile: Optional[bool] = None
    access_policies: list[AccessPolicy] = field(default_factory=list)
    registers: list[Union[Register, RegisterFile]] = field(default_factory=list)
    misalignment_allowed: bool = True
    display_name: Optional[str] = None
    description: Optional[str] = None
    parameters: list[Parameter] = field(default_factory=list)
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
    description: Optional[str] = None
    parameters: list[Parameter] = field(default_factory=list)
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


MemoryMapItem = Union["Bank", AddressBlock, SubspaceMap]


@dataclass
class Bank:
    """ipxact:bank - a bank of address blocks or nested banks, aligned serially or in parallel."""

    name: str
    bank_alignment: BankAlignment
    items: list[MemoryMapItem] = field(default_factory=list)
    usage: Optional[UsageType] = None
    volatile: Optional[bool] = None
    access_policies: list[AccessPolicy] = field(default_factory=list)
    parameters: list[Parameter] = field(default_factory=list)
    display_name: Optional[str] = None
    description: Optional[str] = None
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class MemoryRemap:
    """ipxact:memoryRemap - additional memoryMap content that only applies in given modes."""

    name: str
    mode_refs: list[ModeRef] = field(default_factory=list)
    items: list[MemoryMapItem] = field(default_factory=list)
    display_name: Optional[str] = None
    description: Optional[str] = None
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class MemoryMap:
    """ipxact:memoryMap - a component's addressable space, made of address blocks/banks/subspace maps."""

    name: str
    items: list[MemoryMapItem] = field(default_factory=list)
    memory_remaps: list[MemoryRemap] = field(default_factory=list)
    address_unit_bits: Optional[Expression] = None
    shared: Optional[SharedType] = None
    display_name: Optional[str] = None
    description: Optional[str] = None
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class LocalMemoryMap:
    """ipxact:localMemoryMap - the memory map local to one address space (accessible only via it)."""

    name: str
    items: list[Union[Bank, AddressBlock]] = field(default_factory=list)
    display_name: Optional[str] = None
    description: Optional[str] = None
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class Segment:
    """ipxact:segment - a named sub-range of an address space."""

    name: str
    address_offset: Expression
    range: Expression
    display_name: Optional[str] = None
    description: Optional[str] = None
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
    description: Optional[str] = None
    parameters: list[Parameter] = field(default_factory=list)
    vendor_extensions: list[VendorExtension] = field(default_factory=list)
