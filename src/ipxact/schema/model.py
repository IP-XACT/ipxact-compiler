from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .common import FileBuilder, LocalReference, Location, ModuleParameter, Parameter, TextValue, VendorExtension
from .ports import Port
from .vlnv import VLNVRef


@dataclass
class View:
    """ipxact:view - names an environment and links it to instantiations (model.xsd modelType)."""

    name: str
    env_identifiers: list[TextValue] = field(default_factory=list)
    component_instantiation_ref: Optional[str] = None
    design_instantiation_ref: Optional[str] = None
    design_configuration_instantiation_ref: Optional[str] = None
    display_name: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    xml_id: Optional[str] = None
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class ClearboxElementRef:
    """ipxact:clearboxElementRef - where a clearbox element can be reached in this instantiation."""

    name: str
    locations: list[Location] = field(default_factory=list)
    xml_id: Optional[str] = None
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class ComponentInstantiation:
    """ipxact:componentInstantiation - HDL implementation metadata for one view."""

    name: str
    is_virtual: bool = False
    language: Optional[str] = None
    language_strict: bool = False
    library_name: Optional[str] = None
    package_name: Optional[str] = None
    module_name: Optional[str] = None
    architecture_name: Optional[str] = None
    configuration_name: Optional[str] = None
    module_parameters: list[ModuleParameter] = field(default_factory=list)
    default_file_builders: list[FileBuilder] = field(default_factory=list)
    file_set_refs: list[LocalReference] = field(default_factory=list)
    constraint_set_refs: list[LocalReference] = field(default_factory=list)
    clearbox_element_refs: list[ClearboxElementRef] = field(default_factory=list)
    parameters: list[Parameter] = field(default_factory=list)
    display_name: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    xml_id: Optional[str] = None
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class DesignInstantiation:
    """ipxact:designInstantiation - references an IP-XACT design document for one view."""

    name: str
    design_ref: VLNVRef
    display_name: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    xml_id: Optional[str] = None
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class DesignConfigurationInstantiation:
    """ipxact:designConfigurationInstantiation - references a design configuration for one view."""

    name: str
    design_configuration_ref: VLNVRef
    language: Optional[str] = None
    language_strict: bool = False
    parameters: list[Parameter] = field(default_factory=list)
    display_name: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    xml_id: Optional[str] = None
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class Model:
    """ipxact:model - views, their instantiations, and the component's physical ports."""

    views: list[View] = field(default_factory=list)
    component_instantiations: list[ComponentInstantiation] = field(default_factory=list)
    design_instantiations: list[DesignInstantiation] = field(default_factory=list)
    design_configuration_instantiations: list[DesignConfigurationInstantiation] = field(
        default_factory=list
    )
    ports: list[Port] = field(default_factory=list)
