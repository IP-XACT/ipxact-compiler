from __future__ import annotations

from typing import Callable, Optional, TypeVar

from lxml import etree

from ..schema.common import (
    AccessHandle,
    ArrayBound,
    ArrayDim,
    Assertion,
    BuildCommand,
    Choice,
    ChoiceEnumeration,
    DefinitionRef,
    Define,
    Expression,
    FieldReference,
    File,
    FileBuilder,
    FileSet,
    FileSetRefGroup,
    FileType,
    Function,
    FunctionArgument,
    IndexedRef,
    LocalReference,
    Location,
    MemoryArray,
    ModeRef,
    Parameter,
    PartSelect,
    Range,
    Slice,
    SourceFile,
    SubPortReference,
    TextValue,
    Vector,
)
from ..schema.ports import (
    CellSpecification,
    DriveConstraint,
    FlowControlFlag,
    LevelFlag,
    LoadConstraint,
    Payload,
    Protocol,
    Qualifier,
    TimingConstraint,
    UserFlag,
)
from ..schema.vlnv import VLNV, VLNVRef

NAMESPACE = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"
XML_NAMESPACE = "http://www.w3.org/XML/1998/namespace"
XML_ID = f"{{{XML_NAMESPACE}}}id"


def qn(tag: str) -> str:
    """Build a namespace-qualified IP-XACT tag, e.g. qn("component") -> "{ns}component"."""
    return f"{{{NAMESPACE}}}{tag}"


def child(elem: etree._Element, tag: str) -> Optional[etree._Element]:
    return elem.find(qn(tag))


def children(elem: etree._Element, tag: str) -> list[etree._Element]:
    return elem.findall(qn(tag))


T = TypeVar("T")


def parse_children(
    elem: etree._Element, container_tag: str, item_tag: str, parse_fn: Callable[[etree._Element], T]
) -> list[T]:
    """Parse item_tag children of elem's optional container_tag container, or [] if absent.

    Covers the common IP-XACT shape of an optional wrapper element (e.g. busInterfaces)
    holding one or more repeated items (e.g. busInterface).
    """
    container = child(elem, container_tag)
    if container is None:
        return []
    return [parse_fn(e) for e in children(container, item_tag)]


def elem_text(elem: Optional[etree._Element]) -> Optional[str]:
    """Return an element's text content, stripped, or None if the element is missing or has no text.

    All direct text nodes are joined, not just ``elem.text``, because a comment or processing
    instruction splits the text and pushes the rest onto that node's ``.tail``
    (``<vendor><!-- x -->acme</vendor>`` has ``elem.text`` None). The result is stripped
    because pretty-printed files wrap values in whitespace (``"\\n  required\\n"``), which
    would otherwise break enum construction such as ``Direction(...)``.
    """
    if elem is None:
        return None
    if len(elem) == 0:  # only text, no child nodes
        return elem.text.strip() if elem.text is not None else None
    # With child nodes (Comments, PI, etc)
    parts = elem.xpath("text()")
    if not parts:
        return None
    return "".join(parts).strip()


def text(elem: Optional[etree._Element], tag: str) -> Optional[str]:
    if elem is None:
        return None
    return elem_text(child(elem, tag))


def texts(elem: etree._Element, tag: str) -> list[str]:
    return [t for t in (elem_text(e) for e in children(elem, tag)) if t is not None]


def as_bool(value: Optional[str], default: Optional[bool] = None) -> Optional[bool]:
    if value is None:
        return default
    return value.strip().lower() in ("true", "1")


def bool_text(elem: etree._Element, tag: str, default: Optional[bool] = None) -> Optional[bool]:
    return as_bool(text(elem, tag), default)


def attr_bool(elem: etree._Element, name: str, default: bool = False) -> bool:
    return as_bool(elem.get(name), default)


def xml_id(elem: Optional[etree._Element]) -> Optional[str]:
    """The element's xml:id attribute, or None."""
    return elem.get(XML_ID) if elem is not None else None


def other_attributes(elem: etree._Element) -> dict[str, str]:
    """Attributes from other namespaces (the schema's ``any.att``), keyed by ``{namespace}name``.

    IP-XACT's own attributes are unqualified and xml:id is modeled separately, so both are left out.
    """
    return {
        str(name): str(value)
        for name, value in elem.attrib.items()
        if str(name).startswith("{") and not str(name).startswith(f"{{{XML_NAMESPACE}}}")
    }


def parse_expression(elem: etree._Element) -> Expression:
    """An expression-typed element (value plus its optional bounds, xml:id and foreign attributes)."""
    return Expression(
        value=elem_text(elem) or "",
        minimum=elem.get("minimum"),
        maximum=elem.get("maximum"),
        xml_id=xml_id(elem),
        other_attributes=other_attributes(elem),
    )


def parse_optional_expression(elem: Optional[etree._Element]) -> Optional[Expression]:
    return parse_expression(elem) if elem is not None else None


def expr(elem: Optional[etree._Element], tag: str) -> Optional[Expression]:
    """Expression analogue of text(): the tag child of elem parsed as an Expression, or None."""
    if elem is None:
        return None
    return parse_optional_expression(child(elem, tag))


def exprs(elem: etree._Element, tag: str) -> list[Expression]:
    return [parse_expression(e) for e in children(elem, tag)]


def required_expr(elem: etree._Element, tag: str) -> Expression:
    """Like expr(), but an absent element gives an empty Expression for required schema fields."""
    return expr(elem, tag) or Expression("")


def text_value(elem: etree._Element) -> TextValue:
    return TextValue(value=elem_text(elem) or "", xml_id=xml_id(elem))


def text_values(elem: etree._Element, tag: str) -> list[TextValue]:
    return [text_value(e) for e in children(elem, tag)]


def parse_name_group(elem: etree._Element) -> dict[str, Optional[str]]:
    """The displayName/shortDescription/description of a nameGroup, as constructor kwargs."""
    return dict(
        display_name=text(elem, "displayName"),
        short_description=text(elem, "shortDescription"),
        description=text(elem, "description"),
    )


def parse_vlnv(elem: etree._Element) -> VLNV:
    """documentNameGroup - vendor/library/name/version as child elements."""
    return VLNV(
        vendor=text(elem, "vendor") or "",
        library=text(elem, "library") or "",
        name=text(elem, "name") or "",
        version=text(elem, "version") or "",
    )


def parse_configurable_element_values(elem: etree._Element) -> dict[str, Expression]:
    """ipxact:configurableElementValues - a set of parameterId-keyed override expressions."""
    config_values: dict[str, Expression] = {}
    values_container = child(elem, "configurableElementValues")
    if values_container is not None:
        for value_elem in children(values_container, "configurableElementValue"):
            reference_id = value_elem.get("referenceId")
            if reference_id is not None:
                config_values[reference_id] = parse_expression(value_elem)
    return config_values


def parse_vlnv_ref(elem: etree._Element) -> VLNVRef:
    """libraryRefType/configurableLibraryRefType - vendor/library/name/version as attributes."""
    return VLNVRef(
        vendor=elem.get("vendor", ""),
        library=elem.get("library", ""),
        name=elem.get("name", ""),
        version=elem.get("version", ""),
        config_element_values=parse_configurable_element_values(elem),
        xml_id=xml_id(elem),
    )


def parse_range(elem: Optional[etree._Element]) -> Optional[Range]:
    """The optional ipxact:range child of elem."""
    range_elem = child(elem, "range") if elem is not None else None
    if range_elem is None:
        return None
    return Range(left=required_expr(range_elem, "left"), right=required_expr(range_elem, "right"))


def parse_vector(elem: etree._Element) -> Vector:
    return Vector(
        left=required_expr(elem, "left"),
        right=required_expr(elem, "right"),
        vector_id=elem.get("vectorId"),
        xml_id=xml_id(elem),
    )


def parse_vectors(elem: etree._Element) -> list[Vector]:
    container = child(elem, "vectors")
    if container is None:
        return []
    return [parse_vector(v) for v in children(container, "vector")]


def parse_array_bound(elem: etree._Element) -> ArrayBound:
    return ArrayBound(
        left=required_expr(elem, "left"),
        right=required_expr(elem, "right"),
        array_id=elem.get("arrayId"),
        xml_id=xml_id(elem),
    )


def parse_array_bounds(elem: etree._Element) -> list[ArrayBound]:
    container = child(elem, "arrays")
    if container is None:
        return []
    return [parse_array_bound(a) for a in children(container, "array")]


def parse_memory_array(elem: Optional[etree._Element]) -> Optional[MemoryArray]:
    """ipxact:array of an address block, register file, register (stride) or field (bitStride)."""
    if elem is None:
        return None
    dims = [ArrayDim(size=parse_expression(d), index_var=d.get("indexVar")) for d in children(elem, "dim")]
    # An lxml element with no children is falsy, so `or` can't pick between the two.
    stride_elem = child(elem, "stride")
    if stride_elem is None:
        stride_elem = child(elem, "bitStride")
    return MemoryArray(dims=dims, stride=parse_optional_expression(stride_elem))


def parse_mode_ref(elem: etree._Element) -> ModeRef:
    priority = elem.get("priority")
    return ModeRef(
        name=elem_text(elem) or "",
        priority=int(priority) if priority is not None else None,
        xml_id=xml_id(elem),
    )


def parse_mode_refs(elem: etree._Element, tag: str = "modeRef") -> list[ModeRef]:
    return [parse_mode_ref(m) for m in children(elem, tag)]


def parse_indices(elem: etree._Element) -> list[Expression]:
    """The index expressions of elem's optional ipxact:indices child."""
    indices = child(elem, "indices")
    if indices is None:
        return []
    return exprs(indices, "index")


def parse_part_select(elem: etree._Element) -> Optional[PartSelect]:
    part_select = child(elem, "partSelect")
    if part_select is None:
        return None
    return PartSelect(range=parse_range(part_select), indices=parse_indices(part_select), xml_id=xml_id(part_select))


def parse_sub_port_reference(elem: etree._Element) -> SubPortReference:
    return SubPortReference(
        sub_port_ref=elem.get("subPortRef", ""), part_select=parse_part_select(elem), xml_id=xml_id(elem)
    )


def parse_sub_port_references(elem: etree._Element, tag: str = "subPortReference") -> list[SubPortReference]:
    return [parse_sub_port_reference(s) for s in children(elem, tag)]


def parse_indexed_ref(elem: etree._Element, attribute: str) -> IndexedRef:
    """addressBlockRef/bankRef/registerFileRef/registerRef/fieldRef - the name is in ``attribute``."""
    return IndexedRef(name=elem.get(attribute, ""), indices=parse_indices(elem), xml_id=xml_id(elem))


def parse_field_reference(elem: etree._Element) -> FieldReference:
    """fieldReferenceGroup / fieldSliceReferenceGroup content, from any of the elements using it."""

    def ref(tag: str) -> Optional[IndexedRef]:
        ref_elem = child(elem, tag)
        return parse_indexed_ref(ref_elem, tag) if ref_elem is not None else None

    def attr_of(tag: str) -> Optional[str]:
        ref_elem = child(elem, tag)
        return ref_elem.get(tag) if ref_elem is not None else None

    return FieldReference(
        field_ref=ref("fieldRef") or IndexedRef(""),
        register_ref=ref("registerRef"),
        alternate_register_ref=attr_of("alternateRegisterRef"),
        register_file_refs=[parse_indexed_ref(e, "registerFileRef") for e in children(elem, "registerFileRef")],
        address_block_ref=ref("addressBlockRef"),
        bank_refs=[parse_indexed_ref(e, "bankRef") for e in children(elem, "bankRef")],
        memory_map_ref=attr_of("memoryMapRef"),
        memory_remap_ref=attr_of("memoryRemapRef"),
        address_space_ref=attr_of("addressSpaceRef"),
        range=parse_range(elem),
    )


def parse_slice(elem: etree._Element) -> Slice:
    path_segments = child(elem, "pathSegments")
    return Slice(
        path_segments=exprs(path_segments, "pathSegment") if path_segments is not None else [],
        range=parse_range(elem),
        xml_id=xml_id(elem),
    )


def parse_location(elem: etree._Element) -> Location:
    return Location(slices=[parse_slice(s) for s in children(elem, "slice")], xml_id=xml_id(elem))


def parse_access_handle(elem: etree._Element) -> AccessHandle:
    """simpleAccessHandle (pathSegments), slicedAccessHandle (slices) or portAccessHandle (indices, slices)."""
    path_segments = child(elem, "pathSegments")
    slices = child(elem, "slices")
    return AccessHandle(
        view_refs=text_values(elem, "viewRef"),
        path_segments=exprs(path_segments, "pathSegment") if path_segments is not None else [],
        indices=parse_indices(elem),
        slices=[parse_slice(s) for s in children(slices, "slice")] if slices is not None else [],
        slices_xml_id=xml_id(slices),
        force=attr_bool(elem, "force", True),
        xml_id=xml_id(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def parse_access_handles(elem: etree._Element) -> list[AccessHandle]:
    return parse_children(elem, "accessHandles", "accessHandle", parse_access_handle)


def parse_definition_ref(elem: etree._Element, tag: str) -> Optional[DefinitionRef]:
    """A ``*DefinitionRef`` child (e.g. registerDefinitionRef), or None if absent."""
    ref_elem = child(elem, tag)
    if ref_elem is None:
        return None
    return DefinitionRef(name=elem_text(ref_elem) or "", type_definitions=ref_elem.get("typeDefinitions", ""))


def parse_local_reference(elem: etree._Element) -> LocalReference:
    """fileSetRef / constraintSetRef / busInterfaceRef."""
    return LocalReference(
        local_name=text(elem, "localName") or "",
        xml_id=xml_id(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def parse_vendor_extensions(elem: etree._Element) -> list[str]:
    container = child(elem, "vendorExtensions")
    if container is None:
        return []
    # with_tail=False: the whitespace after an extension in the file is not part of it
    return [etree.tostring(e, encoding="unicode", with_tail=False) for e in container]


def parse_parameter_fields(elem: etree._Element) -> dict:
    """The parameterType content shared by Parameter and ModuleParameter, as constructor kwargs."""
    config_groups = elem.get("configGroups")
    order = elem.get("order")
    return dict(
        name=text(elem, "name") or "",
        value=required_expr(elem, "value"),
        **parse_name_group(elem),
        vectors=parse_vectors(elem),
        arrays=parse_array_bounds(elem),
        parameter_id=elem.get("parameterId"),
        prompt=elem.get("prompt"),
        choice_ref=elem.get("choiceRef"),
        order=float(order) if order is not None else None,
        config_groups=config_groups.split() if config_groups else [],
        minimum=elem.get("minimum"),
        maximum=elem.get("maximum"),
        type=elem.get("type", "string"),
        sign=elem.get("sign"),
        prefix=elem.get("prefix"),
        unit=elem.get("unit"),
        resolve=elem.get("resolve", "immediate"),
        xml_id=xml_id(elem),
        other_attributes=other_attributes(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def parse_parameter(elem: etree._Element) -> Parameter:
    return Parameter(**parse_parameter_fields(elem))


def parse_parameters(elem: etree._Element) -> list[Parameter]:
    container = child(elem, "parameters")
    if container is None:
        return []
    return [parse_parameter(p) for p in children(container, "parameter")]


def parse_choice_enumeration(elem: etree._Element) -> ChoiceEnumeration:
    return ChoiceEnumeration(value=parse_expression(elem), text=elem.get("text"), help=elem.get("help"))


def parse_choice(elem: etree._Element) -> Choice:
    return Choice(
        name=text(elem, "name") or "",
        enumerations=[parse_choice_enumeration(e) for e in children(elem, "enumeration")],
        xml_id=xml_id(elem),
    )


def parse_choices(elem: etree._Element) -> list[Choice]:
    container = child(elem, "choices")
    if container is None:
        return []
    return [parse_choice(c) for c in children(container, "choice")]


def parse_assertion(elem: etree._Element) -> Assertion:
    return Assertion(
        name=text(elem, "name") or "",
        assert_expression=required_expr(elem, "assert"),
        **parse_name_group(elem),
        xml_id=xml_id(elem),
    )


def parse_assertions(elem: etree._Element) -> list[Assertion]:
    container = child(elem, "assertions")
    if container is None:
        return []
    return [parse_assertion(a) for a in children(container, "assertion")]


def parse_file_type(elem: Optional[etree._Element]) -> FileType:
    if elem is None:
        return FileType("")
    return FileType(
        value=elem_text(elem) or "", user=elem.get("user"), libext=elem.get("libext"), xml_id=xml_id(elem)
    )


def parse_file_builder(elem: etree._Element) -> FileBuilder:
    """fileBuilderType (defaultFileBuilder) and languageTools/fileBuilder."""
    return FileBuilder(
        file_type=parse_file_type(child(elem, "fileType")),
        command=expr(elem, "command"),
        flags=expr(elem, "flags"),
        replace_default_flags=expr(elem, "replaceDefaultFlags"),
        xml_id=xml_id(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def parse_build_command(elem: Optional[etree._Element]) -> Optional[BuildCommand]:
    if elem is None:
        return None
    flags_elem = child(elem, "flags")
    return BuildCommand(
        command=expr(elem, "command"),
        flags=parse_optional_expression(flags_elem),
        flags_append=as_bool(flags_elem.get("append")) if flags_elem is not None else None,
        replace_default_flags=expr(elem, "replaceDefaultFlags"),
        target_name=text(elem, "targetName"),
    )


def parse_define(elem: etree._Element) -> Define:
    return Define(
        name=text(elem, "name") or "",
        value=required_expr(elem, "value"),
        **parse_name_group(elem),
        xml_id=xml_id(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def parse_file(elem: etree._Element) -> File:
    is_include = child(elem, "isIncludeFile")
    logical_name = child(elem, "logicalName")
    return File(
        name=text(elem, "name") or "",
        file_types=[parse_file_type(t) for t in children(elem, "fileType")],
        is_structural=bool_text(elem, "isStructural", False),
        is_include_file=is_include is not None and as_bool(elem_text(is_include), False) is True,
        include_has_external_declarations=is_include is not None
        and attr_bool(is_include, "externalDeclarations", False),
        logical_name=elem_text(logical_name),
        logical_name_default=logical_name is not None and attr_bool(logical_name, "default", False),
        exported_names=text_values(elem, "exportedName"),
        build_command=parse_build_command(child(elem, "buildCommand")),
        dependencies=text_values(elem, "dependency"),
        defines=[parse_define(d) for d in children(elem, "define")],
        image_types=text_values(elem, "imageType"),
        description=text(elem, "description"),
        file_id=elem.get("fileId"),
        xml_id=xml_id(elem),
        other_attributes=other_attributes(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def parse_function_argument(elem: etree._Element) -> FunctionArgument:
    return FunctionArgument(
        name=text(elem, "name") or "",
        value=required_expr(elem, "value"),
        data_type=elem.get("dataType", ""),
        **parse_name_group(elem),
        xml_id=xml_id(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def parse_source_file(elem: etree._Element) -> SourceFile:
    return SourceFile(
        source_name=text(elem, "sourceName") or "",
        file_type=parse_file_type(child(elem, "fileType")),
        xml_id=xml_id(elem),
    )


def parse_function(elem: etree._Element) -> Function:
    return Function(
        file_ref=text(elem, "fileRef") or "",
        entry_point=text(elem, "entryPoint"),
        return_type=text(elem, "returnType"),
        arguments=[parse_function_argument(a) for a in children(elem, "argument")],
        disabled=expr(elem, "disabled"),
        source_files=[parse_source_file(s) for s in children(elem, "sourceFile")],
        replicate=attr_bool(elem, "replicate", False),
        xml_id=xml_id(elem),
    )


def parse_file_set(elem: etree._Element) -> FileSet:
    return FileSet(
        name=text(elem, "name") or "",
        groups=text_values(elem, "group"),
        files=[parse_file(f) for f in children(elem, "file")],
        default_file_builders=[parse_file_builder(b) for b in children(elem, "defaultFileBuilder")],
        dependencies=text_values(elem, "dependency"),
        functions=[parse_function(f) for f in children(elem, "function")],
        **parse_name_group(elem),
        xml_id=xml_id(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def parse_file_sets(elem: etree._Element) -> list[FileSet]:
    container = child(elem, "fileSets")
    if container is None:
        return []
    return [parse_file_set(fs) for fs in children(container, "fileSet")]


def parse_file_set_ref_group(elem: etree._Element) -> FileSetRefGroup:
    return FileSetRefGroup(
        group=text(elem, "group"),
        file_set_refs=[parse_local_reference(r) for r in children(elem, "fileSetRef")],
        xml_id=xml_id(elem),
    )


def parse_qualifier(elem: etree._Element) -> Optional[Qualifier]:
    """ipxact:qualifier - shared by component ports, abstraction definition logical ports and packet fields."""
    container = child(elem, "qualifier")
    if container is None:
        return None
    is_reset_elem = child(container, "isReset")
    is_clock_en_elem = child(container, "isClockEn")
    is_power_en_elem = child(container, "isPowerEn")
    is_flow_control_elem = child(container, "isFlowControl")
    is_user_elem = child(container, "isUser")
    return Qualifier(
        is_address=bool_text(container, "isAddress"),
        is_data=bool_text(container, "isData"),
        is_clock=bool_text(container, "isClock"),
        is_reset=(
            LevelFlag(value=as_bool(elem_text(is_reset_elem)) or False, level=is_reset_elem.get("level"))
            if is_reset_elem is not None
            else None
        ),
        is_valid=bool_text(container, "isValid"),
        is_interrupt=bool_text(container, "isInterrupt"),
        is_clock_en=(
            LevelFlag(
                value=as_bool(elem_text(is_clock_en_elem)) or False,
                level=is_clock_en_elem.get("level"),
                power_domain_ref=is_clock_en_elem.get("powerDomainRef"),
            )
            if is_clock_en_elem is not None
            else None
        ),
        is_power_en=(
            LevelFlag(
                value=as_bool(elem_text(is_power_en_elem)) or False,
                level=is_power_en_elem.get("level"),
                power_domain_ref=is_power_en_elem.get("powerDomainRef"),
            )
            if is_power_en_elem is not None
            else None
        ),
        is_opcode=bool_text(container, "isOpcode"),
        is_protection=bool_text(container, "isProtection"),
        is_flow_control=(
            FlowControlFlag(
                value=as_bool(elem_text(is_flow_control_elem)) or False,
                flow_type=is_flow_control_elem.get("flowType"),
                user=is_flow_control_elem.get("user"),
            )
            if is_flow_control_elem is not None
            else None
        ),
        is_user=(
            UserFlag(value=as_bool(elem_text(is_user_elem)) or False, user=is_user_elem.get("user"))
            if is_user_elem is not None
            else None
        ),
        is_request=bool_text(container, "isRequest"),
        is_response=bool_text(container, "isResponse"),
        xml_id=xml_id(container),
    )


def parse_cell_specification(elem: Optional[etree._Element]) -> CellSpecification:
    if elem is None:
        return CellSpecification()
    cell_function_elem = child(elem, "cellFunction")
    cell_class_elem = child(elem, "cellClass")
    return CellSpecification(
        cell_function=elem_text(cell_function_elem),
        cell_function_other=cell_function_elem.get("other") if cell_function_elem is not None else None,
        cell_class=elem_text(cell_class_elem),
        cell_strength=elem.get("cellStrength"),
    )


def parse_drive_constraint(elem: etree._Element) -> Optional[DriveConstraint]:
    container = child(elem, "driveConstraint")
    if container is None:
        return None
    return DriveConstraint(cell=parse_cell_specification(child(container, "cellSpecification")))


def parse_load_constraint(elem: etree._Element) -> Optional[LoadConstraint]:
    container = child(elem, "loadConstraint")
    if container is None:
        return None
    return LoadConstraint(
        cell=parse_cell_specification(child(container, "cellSpecification")),
        count=expr(container, "count") or Expression("3"),
    )


def parse_timing_constraints(elem: etree._Element) -> list[TimingConstraint]:
    return [
        TimingConstraint(
            value=elem_text(t) or "",
            clock_name=t.get("clockName", ""),
            clock_edge=t.get("clockEdge"),
            delay_type=t.get("delayType"),
            xml_id=xml_id(t),
        )
        for t in children(elem, "timingConstraint")
    ]


def parse_payload(elem: Optional[etree._Element]) -> Optional[Payload]:
    if elem is None:
        return None
    extension_elem = child(elem, "extension")
    return Payload(
        type=text(elem, "type") or "",
        name=text(elem, "name"),
        extension=elem_text(extension_elem),
        extension_mandatory=attr_bool(extension_elem, "mandatory", False) if extension_elem is not None else False,
        vendor_extensions=parse_vendor_extensions(elem),
    )


def parse_protocol(elem: etree._Element) -> Optional[Protocol]:
    container = child(elem, "protocol")
    if container is None:
        return None
    protocol_type_elem = child(container, "protocolType")
    return Protocol(
        protocol_type=elem_text(protocol_type_elem) or "",
        custom_type_name=protocol_type_elem.get("custom") if protocol_type_elem is not None else None,
        payload=parse_payload(child(container, "payload")),
    )
