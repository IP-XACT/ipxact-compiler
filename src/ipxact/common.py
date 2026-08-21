from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

# IP-XACT "expression" types (unsignedIntExpression, stringExpression, ...) are strings that
# may be a literal or reference a parameter / contain arithmetic. Kept as raw strings for now;
# resolving them against a parameter scope is a separate concern for a future pass.
Expression = str

# ipxact:vendorExtensions content is vendor-defined, opaque XML. Each extension is kept as a
# raw serialized XML fragment rather than modeled, since its schema is not IP-XACT's to define.
VendorExtension = str


@dataclass
class Vector:
    """ipxact:vector - one [left:right] bit range (commonStructures vector, port.xsd extendedVectorsType)."""

    left: Expression
    right: Expression
    vector_id: Optional[str] = None


@dataclass
class ArrayBound:
    """ipxact:array (parameter/moduleParameter flavor) - one [left:right] array dimension."""

    left: Expression
    right: Expression
    array_id: Optional[str] = None


@dataclass
class ArrayDim:
    """ipxact:dim - one dimension of a C-style multidimensional array (memoryMap.xsd)."""

    size: Expression
    index_var: Optional[str] = None


@dataclass
class MemoryArray:
    """ipxact:array (memoryMap.xsd flavor) - dims and stride for an array of registers/fields/etc."""

    dims: list[ArrayDim] = field(default_factory=list)
    stride: Optional[Expression] = None


@dataclass
class ModeRef:
    """ipxact:modeRef - a reference to a mode, with a priority used to order overlapping refs."""

    name: str
    priority: int


@dataclass
class PartSelect:
    """ipxact:partSelect - a bit-range and/or index selection into a port or subPort."""

    range_left: Optional[Expression] = None
    range_right: Optional[Expression] = None
    indices: list[Expression] = field(default_factory=list)


@dataclass
class SubPortReference:
    """ipxact:subPortReference - a reference, by name, to one subPort of a structured port."""

    sub_port_ref: str
    part_select: Optional[PartSelect] = None


@dataclass
class ChoiceEnumeration:
    """ipxact:enumeration - one legal value within an ipxact:choice."""

    value: Expression
    text: Optional[str] = None
    help: Optional[str] = None


@dataclass
class Choice:
    """ipxact:choice - a named, enumerated set of legal values, referenced via choiceRef."""

    name: str
    enumerations: list[ChoiceEnumeration] = field(default_factory=list)


@dataclass
class Assertion:
    """ipxact:assertion - an expression describing a valid parameter value setting."""

    name: str
    assert_expression: Expression
    display_name: Optional[str] = None
    description: Optional[str] = None


@dataclass
class Parameter:
    """ipxact:parameter - a name/value pair whose value is an expression (commonStructures parameterType)."""

    name: str
    value: Expression
    display_name: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    vectors: list[Vector] = field(default_factory=list)
    arrays: list[ArrayBound] = field(default_factory=list)
    parameter_id: Optional[str] = None
    prompt: Optional[str] = None
    choice_ref: Optional[str] = None
    order: Optional[float] = None
    config_groups: list[str] = field(default_factory=list)
    minimum: Optional[str] = None
    maximum: Optional[str] = None
    type: str = "string"  # formatType: bit/byte/shortint/int/longint/shortreal/real/string
    sign: Optional[str] = None  # signType: signed/unsigned
    prefix: Optional[str] = None
    unit: Optional[str] = None
    resolve: str = "immediate"  # immediate/user/generated
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class ModuleParameter(Parameter):
    """ipxact:moduleParameter - a Parameter plus HDL-facing type metadata (moduleParameterType)."""

    data_type: Optional[str] = None
    usage_type: str = "typed"  # nontyped/typed/runtime
    data_type_definition: Optional[str] = None
    constrained: list[str] = field(default_factory=list)


@dataclass
class File:
    """ipxact:file - a reference to a source file or directory within a fileSet."""

    name: str
    file_types: list[str] = field(default_factory=list)
    is_structural: bool = False
    is_include_file: bool = False
    include_has_external_declarations: bool = False
    logical_name: Optional[str] = None
    exported_names: list[str] = field(default_factory=list)
    build_command: Optional[str] = None
    build_flags: Optional[str] = None
    dependencies: list[str] = field(default_factory=list)
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class FileBuilder:
    """ipxact:defaultFileBuilder - default build command/flags for files of a given fileType."""

    file_type: str
    command: Optional[str] = None
    flags: Optional[str] = None
    replace_default_flags: Optional[Expression] = None


@dataclass
class FileSet:
    """ipxact:fileSet - a named collection of files, referenced from a componentInstantiation."""

    name: str
    groups: list[str] = field(default_factory=list)
    files: list[File] = field(default_factory=list)
    default_file_builders: list[FileBuilder] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    display_name: Optional[str] = None
    description: Optional[str] = None
    vendor_extensions: list[VendorExtension] = field(default_factory=list)
