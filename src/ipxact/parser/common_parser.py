from __future__ import annotations

from typing import Callable, Optional, TypeVar

from lxml import etree

from ..schema.common import (
    ArrayBound,
    Assertion,
    Choice,
    ChoiceEnumeration,
    File,
    FileBuilder,
    FileSet,
    ModeRef,
    Parameter,
    PartSelect,
    SubPortReference,
    Vector,
)
from ..schema.vlnv import VLNV, VLNVRef

NAMESPACE = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"


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


def text(elem: Optional[etree._Element], tag: str) -> Optional[str]:
    if elem is None:
        return None
    found = child(elem, tag)
    return found.text if found is not None else None


def texts(elem: etree._Element, tag: str) -> list[str]:
    return [e.text for e in children(elem, tag) if e.text is not None]


def as_bool(value: Optional[str], default: Optional[bool] = None) -> Optional[bool]:
    if value is None:
        return default
    return value.strip().lower() in ("true", "1")


def bool_text(elem: etree._Element, tag: str, default: Optional[bool] = None) -> Optional[bool]:
    return as_bool(text(elem, tag), default)


def attr_bool(elem: etree._Element, name: str, default: bool = False) -> bool:
    return as_bool(elem.get(name), default)


def parse_vlnv(elem: etree._Element) -> VLNV:
    """documentNameGroup - vendor/library/name/version as child elements."""
    return VLNV(
        vendor=text(elem, "vendor") or "",
        library=text(elem, "library") or "",
        name=text(elem, "name") or "",
        version=text(elem, "version") or "",
    )


def parse_vlnv_ref(elem: etree._Element) -> VLNVRef:
    """libraryRefType/configurableLibraryRefType - vendor/library/name/version as attributes."""
    config_values: dict[str, str] = {}
    values_container = child(elem, "configurableElementValues")
    if values_container is not None:
        for value_elem in children(values_container, "configurableElementValue"):
            reference_id = value_elem.get("referenceId")
            if reference_id is not None:
                config_values[reference_id] = value_elem.text or ""
    return VLNVRef(
        vendor=elem.get("vendor", ""),
        library=elem.get("library", ""),
        name=elem.get("name", ""),
        version=elem.get("version", ""),
        config_element_values=config_values,
    )


def parse_vector(elem: etree._Element) -> Vector:
    return Vector(left=text(elem, "left") or "", right=text(elem, "right") or "", vector_id=elem.get("vectorId"))


def parse_vectors(elem: etree._Element) -> list[Vector]:
    container = child(elem, "vectors")
    if container is None:
        return []
    return [parse_vector(v) for v in children(container, "vector")]


def parse_array_bound(elem: etree._Element) -> ArrayBound:
    return ArrayBound(left=text(elem, "left") or "", right=text(elem, "right") or "", array_id=elem.get("arrayId"))


def parse_array_bounds(elem: etree._Element) -> list[ArrayBound]:
    container = child(elem, "arrays")
    if container is None:
        return []
    return [parse_array_bound(a) for a in children(container, "array")]


def parse_mode_ref(elem: etree._Element) -> ModeRef:
    priority = elem.get("priority")
    return ModeRef(name=elem.text or "", priority=int(priority) if priority is not None else 0)


def parse_mode_refs(elem: etree._Element, tag: str = "modeRef") -> list[ModeRef]:
    return [parse_mode_ref(m) for m in children(elem, tag)]


def parse_part_select(elem: etree._Element) -> Optional[PartSelect]:
    part_select = child(elem, "partSelect")
    if part_select is None:
        return None
    range_elem = child(part_select, "range")
    indices_elem = child(part_select, "indices")
    indices = texts(indices_elem, "index") if indices_elem is not None else []
    return PartSelect(
        range_left=text(range_elem, "left") if range_elem is not None else None,
        range_right=text(range_elem, "right") if range_elem is not None else None,
        indices=indices,
    )


def parse_sub_port_reference(elem: etree._Element) -> SubPortReference:
    return SubPortReference(sub_port_ref=elem.get("subPortRef", ""), part_select=parse_part_select(elem))


def parse_sub_port_references(elem: etree._Element, tag: str = "subPortReference") -> list[SubPortReference]:
    return [parse_sub_port_reference(s) for s in children(elem, tag)]


def parse_vendor_extensions(elem: etree._Element) -> list[str]:
    container = child(elem, "vendorExtensions")
    if container is None:
        return []
    return [etree.tostring(e, encoding="unicode") for e in container]


def parse_parameter(elem: etree._Element) -> Parameter:
    config_groups = elem.get("configGroups")
    order = elem.get("order")
    return Parameter(
        name=text(elem, "name") or "",
        value=text(elem, "value") or "",
        display_name=text(elem, "displayName"),
        short_description=text(elem, "shortDescription"),
        description=text(elem, "description"),
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
        vendor_extensions=parse_vendor_extensions(elem),
    )


def parse_parameters(elem: etree._Element) -> list[Parameter]:
    container = child(elem, "parameters")
    if container is None:
        return []
    return [parse_parameter(p) for p in children(container, "parameter")]


def parse_choice_enumeration(elem: etree._Element) -> ChoiceEnumeration:
    return ChoiceEnumeration(value=elem.text or "", text=elem.get("text"), help=elem.get("help"))


def parse_choice(elem: etree._Element) -> Choice:
    return Choice(
        name=text(elem, "name") or "",
        enumerations=[parse_choice_enumeration(e) for e in children(elem, "enumeration")],
    )


def parse_choices(elem: etree._Element) -> list[Choice]:
    container = child(elem, "choices")
    if container is None:
        return []
    return [parse_choice(c) for c in children(container, "choice")]


def parse_assertion(elem: etree._Element) -> Assertion:
    return Assertion(
        name=text(elem, "name") or "",
        assert_expression=text(elem, "assert") or "",
        display_name=text(elem, "displayName"),
        description=text(elem, "description"),
    )


def parse_assertions(elem: etree._Element) -> list[Assertion]:
    container = child(elem, "assertions")
    if container is None:
        return []
    return [parse_assertion(a) for a in children(container, "assertion")]


def parse_file_builder(elem: etree._Element) -> FileBuilder:
    return FileBuilder(
        file_type=text(elem, "fileType") or "",
        command=text(elem, "command"),
        flags=text(elem, "flags"),
        replace_default_flags=text(elem, "replaceDefaultFlags"),
    )


def parse_file(elem: etree._Element) -> File:
    is_include = child(elem, "isIncludeFile")
    build_command = child(elem, "buildCommand")
    return File(
        name=text(elem, "name") or "",
        file_types=[t.text or "" for t in children(elem, "fileType")],
        is_structural=bool_text(elem, "isStructural", False) or False,
        is_include_file=is_include is not None and as_bool(is_include.text, False) is True,
        include_has_external_declarations=is_include is not None
        and attr_bool(is_include, "externalDeclarations", False),
        logical_name=text(elem, "logicalName"),
        exported_names=texts(elem, "exportedName"),
        build_command=text(build_command, "command") if build_command is not None else None,
        build_flags=text(build_command, "flags") if build_command is not None else None,
        vendor_extensions=parse_vendor_extensions(elem),
    )


def parse_file_set(elem: etree._Element) -> FileSet:
    return FileSet(
        name=text(elem, "name") or "",
        groups=texts(elem, "group"),
        files=[parse_file(f) for f in children(elem, "file")],
        default_file_builders=[parse_file_builder(b) for b in children(elem, "defaultFileBuilder")],
        dependencies=texts(elem, "dependency"),
        display_name=text(elem, "displayName"),
        description=text(elem, "description"),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def parse_file_sets(elem: etree._Element) -> list[FileSet]:
    container = child(elem, "fileSets")
    if container is None:
        return []
    return [parse_file_set(fs) for fs in children(container, "fileSet")]
