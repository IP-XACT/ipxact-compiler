from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .common import ModuleParameter, Parameter, VendorExtension
from .ports import Port
from .vlnv import VLNVRef


@dataclass
class View:
    """ipxact:view - names an environment and links it to instantiations (model.xsd modelType)."""

    name: str
    env_identifiers: list[str] = field(default_factory=list)
    component_instantiation_ref: Optional[str] = None
    design_instantiation_ref: Optional[str] = None
    design_configuration_instantiation_ref: Optional[str] = None
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class FileBuilderOverride:
    """ipxact:defaultFileBuilder - override the default build command/flags for one fileType."""

    file_type: str
    command: Optional[str] = None
    flags: Optional[str] = None
    replace_default_flags: Optional[str] = None


@dataclass
class ComponentInstantiation:
    """ipxact:componentInstantiation - HDL implementation metadata for one view."""

    name: str
    is_virtual: bool = False
    language: Optional[str] = None
    library_name: Optional[str] = None
    package_name: Optional[str] = None
    module_name: Optional[str] = None
    architecture_name: Optional[str] = None
    configuration_name: Optional[str] = None
    module_parameters: list[ModuleParameter] = field(default_factory=list)
    default_file_builders: list[FileBuilderOverride] = field(default_factory=list)
    file_set_refs: list[str] = field(default_factory=list)
    constraint_set_refs: list[str] = field(default_factory=list)
    parameters: list[Parameter] = field(default_factory=list)
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class DesignInstantiation:
    """ipxact:designInstantiation - references an IP-XACT design document for one view."""

    name: str
    design_ref: VLNVRef
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class DesignConfigurationInstantiation:
    """ipxact:designConfigurationInstantiation - references a design configuration for one view."""

    name: str
    design_configuration_ref: VLNVRef
    language: Optional[str] = None
    parameters: list[Parameter] = field(default_factory=list)
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
