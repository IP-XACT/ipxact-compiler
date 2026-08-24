from __future__ import annotations

from lxml import etree

from ..schema.designconfig import (
    AbstractorChain,
    AbstractorInstance,
    DesignConfiguration,
    InterconnectionConfiguration,
    InterfaceRef,
    ViewConfiguration,
)
from .common_parser import (
    child,
    children,
    parse_assertions,
    parse_choices,
    parse_configurable_element_values,
    parse_parameters,
    parse_vendor_extensions,
    parse_vlnv,
    parse_vlnv_ref,
    text,
)


def parse_designconfig(root: etree._Element) -> DesignConfiguration:
    """Parse an ipxact:designConfiguration root element into a DesignConfiguration object."""
    design_ref_elem = child(root, "designRef")
    return DesignConfiguration(
        vlnv=parse_vlnv(root),
        design_ref=parse_vlnv_ref(design_ref_elem) if design_ref_elem is not None else None,
        generator_chain_configurations=[
            parse_vlnv_ref(e) for e in children(root, "generatorChainConfiguration")
        ],
        interconnection_configurations=[
            _parse_interconnection_configuration(e) for e in children(root, "interconnectionConfiguration")
        ],
        view_configurations=[_parse_view_configuration(e) for e in children(root, "viewConfiguration")],
        choices=parse_choices(root),
        parameters=parse_parameters(root),
        assertions=parse_assertions(root),
        display_name=text(root, "displayName"),
        short_description=text(root, "shortDescription"),
        description=text(root, "description"),
        vendor_extensions=parse_vendor_extensions(root),
    )


def _parse_interface_ref(elem: etree._Element) -> InterfaceRef:
    return InterfaceRef(
        component_ref=elem.get("componentRef", ""),
        bus_ref=elem.get("busRef", ""),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_abstractor_instance(elem: etree._Element) -> AbstractorInstance:
    return AbstractorInstance(
        instance_name=text(elem, "instanceName") or "",
        abstractor_ref=parse_vlnv_ref(child(elem, "abstractorRef")),
        view_name=text(elem, "viewName") or "",
        display_name=text(elem, "displayName"),
        short_description=text(elem, "shortDescription"),
        description=text(elem, "description"),
    )


def _parse_abstractor_chain(elem: etree._Element) -> AbstractorChain:
    return AbstractorChain(
        abstractors=[_parse_abstractor_instance(e) for e in children(elem, "abstractorInstance")],
        interface_refs=[_parse_interface_ref(e) for e in children(elem, "interfaceRef")],
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_interconnection_configuration(elem: etree._Element) -> InterconnectionConfiguration:
    return InterconnectionConfiguration(
        interconnection_ref=text(elem, "interconnectionRef") or "",
        abstractor_chains=[_parse_abstractor_chain(e) for e in children(elem, "abstractorInstances")],
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_view_configuration(elem: etree._Element) -> ViewConfiguration:
    view_elem = child(elem, "view")
    return ViewConfiguration(
        instance_name=text(elem, "instanceName") or "",
        view_ref=view_elem.get("viewRef", "") if view_elem is not None else "",
        configurable_element_values=(
            parse_configurable_element_values(view_elem) if view_elem is not None else {}
        ),
        vendor_extensions=parse_vendor_extensions(elem),
    )
