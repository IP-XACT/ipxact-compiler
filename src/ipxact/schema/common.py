from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

# ipxact:vendorExtensions content is vendor-defined, opaque XML. Each extension is kept as a
# raw serialized XML fragment rather than modeled, since its schema is not IP-XACT's to define.
VendorExtension = str


@dataclass
class Expression:
    """An IP-XACT expression value (unsignedIntExpression, stringExpression, ...).

    ``value`` is the raw expression text, left unevaluated: it may be a literal or reference a
    parameter / contain arithmetic. ``minimum``/``maximum`` are the optional bounds the schema
    allows on numeric expressions; ``other_attributes`` holds attributes from other namespaces
    (``any.att``), keyed by their ``{namespace}name``.
    """

    value: str
    minimum: Optional[str] = None
    maximum: Optional[str] = None
    xml_id: Optional[str] = None
    other_attributes: dict[str, str] = field(default_factory=dict)

    def __str__(self) -> str:
        return self.value


@dataclass
class TextValue:
    """A plain (non-expression) text element that may carry an xml:id, e.g. viewRef or group."""

    value: str
    xml_id: Optional[str] = None


@dataclass
class Range:
    """ipxact:range - a [left:right] bit range."""

    left: Expression
    right: Expression


@dataclass
class Vector:
    """ipxact:vector - one [left:right] bit range (commonStructures vector, port.xsd extendedVectorsType)."""

    left: Expression
    right: Expression
    vector_id: Optional[str] = None
    xml_id: Optional[str] = None


@dataclass
class ArrayBound:
    """ipxact:array (parameter/port flavor) - one [left:right] array dimension."""

    left: Expression
    right: Expression
    array_id: Optional[str] = None
    xml_id: Optional[str] = None


@dataclass
class ArrayDim:
    """ipxact:dim - one dimension of a C-style multidimensional array (memoryMap.xsd)."""

    size: Expression
    index_var: Optional[str] = None


@dataclass
class MemoryArray:
    """ipxact:array (memoryMap.xsd flavor) - dims and stride for an array of blocks/registers/fields.

    ``stride`` holds ``ipxact:stride`` (address blocks, registers, register files) or
    ``ipxact:bitStride`` (fields).
    """

    dims: list[ArrayDim] = field(default_factory=list)
    stride: Optional[Expression] = None


@dataclass
class ModeRef:
    """ipxact:modeRef - a reference to a mode.

    ``priority`` orders overlapping refs; it is absent on the modeRefs of an initiator's
    addressSpaceRef and a target's memoryMapRef, which have no priority attribute.
    """

    name: str
    priority: Optional[int] = None
    xml_id: Optional[str] = None


@dataclass
class PartSelect:
    """ipxact:partSelect - a bit-range and/or index selection into a port or subPort."""

    range: Optional[Range] = None
    indices: list[Expression] = field(default_factory=list)
    xml_id: Optional[str] = None


@dataclass
class SubPortReference:
    """ipxact:subPortReference - a reference, by name, to one subPort of a structured port."""

    sub_port_ref: str
    part_select: Optional[PartSelect] = None
    xml_id: Optional[str] = None


@dataclass
class IndexedRef:
    """A named reference to a memory-map element, optionally indexed into an array of it.

    Used for addressBlockRef, bankRef, registerFileRef, registerRef and fieldRef. ``indices``
    is empty for bankRef, which has no indices.
    """

    name: str
    indices: list[Expression] = field(default_factory=list)
    xml_id: Optional[str] = None


@dataclass
class FieldReference:
    """A pointer into the memory-map hierarchy down to one field.

    Covers commonStructures.fieldReferenceGroup (indirectAddressRef/indirectDataRef, a field's
    aliasOf, a broadcastTo) and fieldSliceReferenceGroup (mode/fieldSlice and fieldMap/fieldSlice,
    where addressBlockRef/registerRef are required and a trailing bit range is allowed). Python
    fields are left optional in both cases; nothing at this layer enforces which combination the
    source element actually requires.
    """

    field_ref: IndexedRef
    register_ref: Optional[IndexedRef] = None
    alternate_register_ref: Optional[str] = None
    register_file_refs: list[IndexedRef] = field(default_factory=list)
    address_block_ref: Optional[IndexedRef] = None
    bank_refs: list[IndexedRef] = field(default_factory=list)
    memory_map_ref: Optional[str] = None
    memory_remap_ref: Optional[str] = None
    address_space_ref: Optional[str] = None
    range: Optional[Range] = None
    xml_id: Optional[str] = None  # only a broadcastTo has its own xml:id


@dataclass
class Slice:
    """ipxact:slice - a path into the design hierarchy (pathSegments), optionally narrowed to a range."""

    path_segments: list[Expression] = field(default_factory=list)
    range: Optional[Range] = None
    xml_id: Optional[str] = None


@dataclass
class Location:
    """ipxact:location - where a clearbox element can be reached, as one or more slices."""

    slices: list[Slice] = field(default_factory=list)
    xml_id: Optional[str] = None


@dataclass
class AccessHandle:
    """ipxact:accessHandle - the HDL path of an element, for one or more views.

    Covers the three schema flavors: simpleAccessHandle (registers, register files, alternate
    registers, banks) uses ``path_segments``; slicedAccessHandle (address blocks, fields) and
    portAccessHandle (ports) use ``slices``, and ports may add ``indices``.
    """

    view_refs: list[TextValue] = field(default_factory=list)
    path_segments: list[Expression] = field(default_factory=list)
    indices: list[Expression] = field(default_factory=list)
    slices: list[Slice] = field(default_factory=list)
    slices_xml_id: Optional[str] = None
    force: bool = True
    xml_id: Optional[str] = None
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class DefinitionRef:
    """A ``*DefinitionRef`` element - a reference to a definition in a typeDefinitions document.

    When set, the referencing element's own content (fields, registers, ...) comes from that
    definition instead of being written inline.
    """

    name: str
    type_definitions: str


@dataclass
class LocalReference:
    """A reference to a component-local element by ``localName`` (fileSetRef, constraintSetRef,
    busInterfaceRef)."""

    local_name: str
    xml_id: Optional[str] = None
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


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
    xml_id: Optional[str] = None


@dataclass
class Assertion:
    """ipxact:assertion - an expression describing a valid parameter value setting."""

    name: str
    assert_expression: Expression
    display_name: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    xml_id: Optional[str] = None


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
    xml_id: Optional[str] = None
    other_attributes: dict[str, str] = field(default_factory=dict)
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class ModuleParameter(Parameter):
    """ipxact:moduleParameter / ipxact:typeParameter - a Parameter plus HDL-facing type metadata
    (moduleParameterType)."""

    data_type: Optional[str] = None
    usage_type: str = "typed"  # nontyped/typed/runtime
    data_type_definition: Optional[str] = None
    constrained: list[str] = field(default_factory=list)


@dataclass
class FileType:
    """ipxact:fileType - a file's type; ``user`` names it when ``value`` is "user"."""

    value: str
    user: Optional[str] = None
    libext: Optional[str] = None
    xml_id: Optional[str] = None


@dataclass
class BuildCommand:
    """ipxact:buildCommand - how to build one file (overrides its fileSet's default builder)."""

    command: Optional[Expression] = None
    flags: Optional[Expression] = None
    flags_append: Optional[bool] = None
    replace_default_flags: Optional[Expression] = None
    target_name: Optional[str] = None


@dataclass
class Define:
    """ipxact:define - a name/value pair (e.g. a preprocessor define) used when building a file."""

    name: str
    value: Expression
    display_name: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    xml_id: Optional[str] = None
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class File:
    """ipxact:file - a reference to a source file or directory within a fileSet."""

    name: str
    file_types: list[FileType] = field(default_factory=list)
    is_structural: bool = False
    is_include_file: bool = False
    include_has_external_declarations: bool = False
    logical_name: Optional[str] = None
    logical_name_default: bool = False
    exported_names: list[TextValue] = field(default_factory=list)
    build_command: Optional[BuildCommand] = None
    dependencies: list[TextValue] = field(default_factory=list)
    defines: list[Define] = field(default_factory=list)
    image_types: list[TextValue] = field(default_factory=list)
    file_id: Optional[str] = None
    description: Optional[str] = None
    xml_id: Optional[str] = None
    other_attributes: dict[str, str] = field(default_factory=dict)
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class FileBuilder:
    """ipxact:defaultFileBuilder / ipxact:fileBuilder - build command/flags for files of a given
    fileType (in a fileSet, a componentInstantiation, or an executable image's languageTools).

    Only the languageTools flavor (ipxact:fileBuilder) has vendor extensions.
    """

    file_type: FileType
    command: Optional[Expression] = None
    flags: Optional[Expression] = None
    replace_default_flags: Optional[Expression] = None
    xml_id: Optional[str] = None
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class FunctionArgument:
    """ipxact:argument - one argument passed to a fileSet function."""

    name: str
    value: Expression
    data_type: str  # int/unsigned int/long/unsigned long/float/double/char */void *
    display_name: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    xml_id: Optional[str] = None
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class SourceFile:
    """ipxact:sourceFile - a source file to be compiled for a fileSet function."""

    source_name: str
    file_type: FileType
    xml_id: Optional[str] = None


@dataclass
class Function:
    """ipxact:function - a software function generated from (or with) a fileSet."""

    file_ref: str
    entry_point: Optional[str] = None
    return_type: Optional[str] = None  # void/int
    arguments: list[FunctionArgument] = field(default_factory=list)
    disabled: Optional[Expression] = None
    source_files: list[SourceFile] = field(default_factory=list)
    replicate: bool = False
    xml_id: Optional[str] = None


@dataclass
class FileSet:
    """ipxact:fileSet - a named collection of files, referenced from a componentInstantiation."""

    name: str
    groups: list[TextValue] = field(default_factory=list)
    files: list[File] = field(default_factory=list)
    default_file_builders: list[FileBuilder] = field(default_factory=list)
    dependencies: list[TextValue] = field(default_factory=list)
    functions: list[Function] = field(default_factory=list)
    display_name: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    xml_id: Optional[str] = None
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class FileSetRefGroup:
    """ipxact:fileSetRefGroup - fileSets associated with one function (of a target interface or an
    executable image)."""

    group: Optional[str] = None
    file_set_refs: list[LocalReference] = field(default_factory=list)
    xml_id: Optional[str] = None
