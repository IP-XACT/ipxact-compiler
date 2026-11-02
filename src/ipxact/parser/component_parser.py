from __future__ import annotations

from typing import Optional

from lxml import etree

from ..schema.businterface import (
    AbstractionType,
    BusInterface,
    Channel,
    IndirectInterface,
    InitiatorInterface,
    InterfaceMode,
    MirroredInitiatorInterface,
    MirroredTargetInterface,
    MonitorInterface,
    PortMap,
    RemapAddress,
    SystemInterface,
    TargetInterface,
    TransparentBridge,
)
from ..schema.common import Expression, FieldReference, ModuleParameter, SubPortReference
from ..schema.component import Component
from ..schema.component_sections import (
    ClearboxElement,
    ComponentGenerator,
    Cpu,
    CpuRegion,
    ExecutableImage,
    ExternalTypeDefinitionsRef,
    FieldSlice,
    LanguageTools,
    LinkerCommandFile,
    Mode,
    ModeLink,
    OtherClockDriver,
    PortSlice,
    PowerDomain,
    ResetType,
    ResetTypeLink,
    ViewLink,
)
from ..schema.memorymap import (
    AccessPolicy,
    AccessRestriction,
    AccessType,
    AddressBlock,
    AddressSpace,
    AlternateRegister,
    Bank,
    BankAlignment,
    EnumeratedValue,
    Field,
    FieldAccessPolicy,
    LocalMemoryMap,
    MemoryMap,
    MemoryRemap,
    ModifiedWriteValue,
    ReadAction,
    Register,
    RegisterFile,
    Reset,
    Segment,
    SharedType,
    SubspaceMap,
    TestConstraint,
    UsageType,
    WriteValueConstraint,
)
from ..schema.model import (
    ClearboxElementRef,
    ComponentInstantiation,
    DesignConfigurationInstantiation,
    DesignInstantiation,
    Model,
    View,
)
from ..schema.ports import (
    ClockDriver,
    ConstraintSet,
    Direction,
    DomainTypeDef,
    Driver,
    FieldMap,
    Initiative,
    Port,
    PortAccess,
    PowerConstraint,
    ServiceTypeDef,
    SignalTypeDef,
    SingleShotDriver,
    StructPortTypeDef,
    StructuredPort,
    SubPort,
    TransactionalPort,
    TransTypeDef,
    WirePort,
    WireTypeDef,
)
from ..schema.vlnv import VLNVRef
from .common_parser import (
    as_bool,
    attr_bool,
    bool_text,
    child,
    children,
    elem_text,
    expr,
    other_attributes,
    parse_access_handles,
    parse_array_bounds,
    parse_assertions,
    parse_children,
    parse_choices,
    parse_definition_ref,
    parse_drive_constraint,
    parse_optional_expression,
    parse_field_reference,
    parse_file_builder,
    parse_file_set_ref_group,
    parse_file_sets,
    parse_load_constraint,
    parse_local_reference,
    parse_location,
    parse_memory_array,
    parse_mode_refs,
    parse_parameter_fields,
    parse_name_group,
    parse_parameters,
    parse_part_select,
    parse_protocol,
    parse_qualifier,
    parse_range,
    parse_sub_port_references,
    parse_timing_constraints,
    parse_vector,
    parse_vectors,
    parse_vendor_extensions,
    parse_vlnv,
    parse_vlnv_ref,
    qn,
    required_expr,
    text,
    text_value,
    text_values,
    xml_id,
)


def parse_component(root: etree._Element) -> Component:
    """Parse an ipxact:component root element into a Component object."""
    model_elem = child(root, "model")

    return Component(
        vlnv=parse_vlnv(root),
        bus_interfaces=parse_children(root, "busInterfaces", "busInterface", _parse_bus_interface),
        indirect_interfaces=parse_children(
            root, "indirectInterfaces", "indirectInterface", _parse_indirect_interface
        ),
        channels=parse_children(root, "channels", "channel", _parse_channel),
        modes=parse_children(root, "modes", "mode", _parse_mode),
        address_spaces=parse_children(root, "addressSpaces", "addressSpace", _parse_address_space),
        memory_maps=parse_children(root, "memoryMaps", "memoryMap", _parse_memory_map),
        model=_parse_model(model_elem) if model_elem is not None else None,
        component_generators=parse_children(
            root, "componentGenerators", "componentGenerator", _parse_component_generator
        ),
        choices=parse_choices(root),
        file_sets=parse_file_sets(root),
        clearbox_elements=parse_children(root, "clearboxElements", "clearboxElement", _parse_clearbox_element),
        cpus=parse_children(root, "cpus", "cpu", _parse_cpu),
        other_clock_drivers=parse_children(
            root, "otherClockDrivers", "otherClockDriver", _parse_other_clock_driver
        ),
        reset_types=parse_children(root, "resetTypes", "resetType", _parse_reset_type),
        power_domains=parse_children(root, "powerDomains", "powerDomain", _parse_power_domain),
        external_type_definitions=parse_children(
            root, "typeDefinitions", "externalTypeDefinitions", _parse_external_type_definitions_ref
        ),
        parameters=parse_parameters(root),
        assertions=parse_assertions(root),
        **parse_name_group(root),
        xml_id=xml_id(root),
        vendor_extensions=parse_vendor_extensions(root),
    )


# --- bus interfaces ---


def _parse_port_map(elem: etree._Element) -> PortMap:
    logical_port_elem = child(elem, "logicalPort")
    physical_port_elem = child(elem, "physicalPort")
    return PortMap(
        logical_port=text(logical_port_elem, "name") or "" if logical_port_elem is not None else "",
        logical_range=parse_range(logical_port_elem),
        physical_port=text(physical_port_elem, "name") if physical_port_elem is not None else None,
        part_select=parse_part_select(physical_port_elem) if physical_port_elem is not None else None,
        # physicalPort/subPort names its subport via a <name> child, unlike the attribute-based
        # ipxact:subPortReference shape used elsewhere (e.g. FieldMap).
        sub_port_refs=(
            [_parse_port_map_sub_port(s) for s in children(physical_port_elem, "subPort")]
            if physical_port_elem is not None
            else []
        ),
        logical_tie_off=expr(elem, "logicalTieOff"),
        invert=attr_bool(elem, "invert", False),
        is_informative=bool_text(elem, "isInformative", False),
        logical_port_xml_id=xml_id(logical_port_elem),
        physical_port_xml_id=xml_id(physical_port_elem),
        xml_id=xml_id(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_port_map_sub_port(elem: etree._Element) -> SubPortReference:
    return SubPortReference(
        sub_port_ref=text(elem, "name") or "", part_select=parse_part_select(elem), xml_id=xml_id(elem)
    )


def _parse_abstraction_type(elem: etree._Element) -> AbstractionType:
    return AbstractionType(
        abstraction_ref=parse_vlnv_ref(child(elem, "abstractionRef")),
        port_maps=parse_children(elem, "portMaps", "portMap", _parse_port_map),
        view_refs=text_values(elem, "viewRef"),
        xml_id=xml_id(elem),
    )


def _parse_transparent_bridge(elem: etree._Element) -> TransparentBridge:
    return TransparentBridge(
        initiator_ref=elem.get("initiatorRef", ""), xml_id=xml_id(elem), vendor_extensions=parse_vendor_extensions(elem)
    )


def _parse_initiator_interface(elem: etree._Element) -> InitiatorInterface:
    address_space_ref_elem = child(elem, "addressSpaceRef")
    if address_space_ref_elem is None:
        return InitiatorInterface()
    return InitiatorInterface(
        address_space_ref=address_space_ref_elem.get("addressSpaceRef"),
        base_address=expr(address_space_ref_elem, "baseAddress"),
        mode_refs=parse_mode_refs(address_space_ref_elem),
        xml_id=xml_id(address_space_ref_elem),
        vendor_extensions=parse_vendor_extensions(address_space_ref_elem),
    )


def _parse_target_interface(elem: etree._Element) -> TargetInterface:
    memory_map_ref_elem = child(elem, "memoryMapRef")
    return TargetInterface(
        memory_map_ref=memory_map_ref_elem.get("memoryMapRef") if memory_map_ref_elem is not None else None,
        mode_refs=parse_mode_refs(memory_map_ref_elem) if memory_map_ref_elem is not None else [],
        transparent_bridges=[_parse_transparent_bridge(b) for b in children(elem, "transparentBridge")],
        file_set_ref_groups=[parse_file_set_ref_group(g) for g in children(elem, "fileSetRefGroup")],
    )


def _parse_mirrored_target_interface(elem: etree._Element) -> MirroredTargetInterface:
    base_addresses_elem = child(elem, "baseAddresses")
    if base_addresses_elem is None:
        return MirroredTargetInterface()
    remap_addresses = [
        RemapAddress(
            value=required_expr(remap_addresses_elem, "remapAddress"),
            mode_refs=parse_mode_refs(remap_addresses_elem),
            xml_id=xml_id(remap_addresses_elem),
        )
        for remap_addresses_elem in children(base_addresses_elem, "remapAddresses")
    ]
    return MirroredTargetInterface(remap_addresses=remap_addresses, range=expr(base_addresses_elem, "range"))


def _parse_bus_interface(elem: etree._Element) -> BusInterface:
    mode = InterfaceMode.MIRRORED_INITIATOR
    initiator = target = mirrored_target = mirrored_initiator = monitor = None
    system = mirrored_system = None

    if (mode_elem := child(elem, "initiator")) is not None:
        mode = InterfaceMode.INITIATOR
        initiator = _parse_initiator_interface(mode_elem)
    elif (mode_elem := child(elem, "target")) is not None:
        mode = InterfaceMode.TARGET
        target = _parse_target_interface(mode_elem)
    elif (mode_elem := child(elem, "system")) is not None:
        mode = InterfaceMode.SYSTEM
        system = SystemInterface(group=text(mode_elem, "group") or "")
    elif (mode_elem := child(elem, "mirroredTarget")) is not None:
        mode = InterfaceMode.MIRRORED_TARGET
        mirrored_target = _parse_mirrored_target_interface(mode_elem)
    elif (mode_elem := child(elem, "mirroredInitiator")) is not None:
        mode = InterfaceMode.MIRRORED_INITIATOR
        mirrored_initiator = MirroredInitiatorInterface(
            other_attributes=other_attributes(mode_elem),
            content=[
                etree.tostring(e, encoding="unicode", with_tail=False) for e in mode_elem if isinstance(e.tag, str)
            ],
            text=elem_text(mode_elem) or None,
        )
    elif (mode_elem := child(elem, "mirroredSystem")) is not None:
        mode = InterfaceMode.MIRRORED_SYSTEM
        mirrored_system = SystemInterface(group=text(mode_elem, "group") or "")
    elif (mode_elem := child(elem, "monitor")) is not None:
        mode = InterfaceMode.MONITOR
        monitor = MonitorInterface(
            interface_mode=InterfaceMode((mode_elem.get("interfaceMode") or "").strip()),
            group=text(mode_elem, "group"),
        )
    else:
        raise ValueError("busInterface element has no recognized interfaceMode child")

    return BusInterface(
        name=text(elem, "name") or "",
        bus_type=parse_vlnv_ref(child(elem, "busType")),
        mode=mode,
        abstraction_types=parse_children(elem, "abstractionTypes", "abstractionType", _parse_abstraction_type),
        initiator=initiator,
        target=target,
        system=system,
        mirrored_target=mirrored_target,
        mirrored_initiator=mirrored_initiator,
        mirrored_system=mirrored_system,
        monitor=monitor,
        connection_required=bool_text(elem, "connectionRequired", False),
        bits_in_lau=expr(elem, "bitsInLau"),
        # bitSteering defaults to "0" when absent
        bit_steering=expr(elem, "bitSteering") or Expression("0"),
        endianness=text(elem, "endianness"),
        parameters=parse_parameters(elem),
        **parse_name_group(elem),
        xml_id=xml_id(elem),
        other_attributes=other_attributes(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_indirect_interface(elem: etree._Element) -> IndirectInterface:
    return IndirectInterface(
        name=text(elem, "name") or "",
        indirect_address_ref=parse_field_reference(child(elem, "indirectAddressRef")),
        indirect_data_ref=parse_field_reference(child(elem, "indirectDataRef")),
        memory_map_ref=text(elem, "memoryMapRef"),
        transparent_bridges=[_parse_transparent_bridge(b) for b in children(elem, "transparentBridge")],
        bits_in_lau=expr(elem, "bitsInLau"),
        endianness=text(elem, "endianness"),
        **parse_name_group(elem),
        parameters=parse_parameters(elem),
        xml_id=xml_id(elem),
        other_attributes=other_attributes(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_channel(elem: etree._Element) -> Channel:
    return Channel(
        name=text(elem, "name") or "",
        bus_interface_refs=[parse_local_reference(r) for r in children(elem, "busInterfaceRef")],
        **parse_name_group(elem),
        xml_id=xml_id(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


# --- modes ---


def _parse_port_slice(elem: etree._Element) -> PortSlice:
    port_ref_elem = child(elem, "portRef")
    return PortSlice(
        name=text(elem, "name") or "",
        port_ref=port_ref_elem.get("portRef", "") if port_ref_elem is not None else "",
        sub_port_refs=parse_sub_port_references(elem),
        part_select=parse_part_select(elem),
        **parse_name_group(elem),
        xml_id=xml_id(elem),
    )


def _parse_field_slice(elem: etree._Element) -> FieldSlice:
    return FieldSlice(
        name=text(elem, "name") or "",
        field_ref=parse_field_reference(elem),
        **parse_name_group(elem),
        xml_id=xml_id(elem),
    )


def _parse_mode(elem: etree._Element) -> Mode:
    return Mode(
        name=text(elem, "name") or "",
        port_slices=[_parse_port_slice(e) for e in children(elem, "portSlice")],
        field_slices=[_parse_field_slice(e) for e in children(elem, "fieldSlice")],
        condition=expr(elem, "condition"),
        **parse_name_group(elem),
        xml_id=xml_id(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


# --- memory maps ---


def _parse_access_policy(elem: etree._Element) -> AccessPolicy:
    access = text(elem, "access")
    return AccessPolicy(
        mode_refs=parse_mode_refs(elem),
        access=AccessType(access) if access else None,
        xml_id=xml_id(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_access_policies(elem: etree._Element) -> list[AccessPolicy]:
    return parse_children(elem, "accessPolicies", "accessPolicy", _parse_access_policy)


def _parse_reset(elem: etree._Element) -> Reset:
    return Reset(
        value=required_expr(elem, "value"),
        mask=expr(elem, "mask"),
        reset_type_ref=elem.get("resetTypeRef"),
        xml_id=xml_id(elem),
    )


def _parse_enumerated_value(elem: etree._Element) -> EnumeratedValue:
    return EnumeratedValue(
        name=text(elem, "name") or "",
        value=required_expr(elem, "value"),
        usage=elem.get("usage", "read-write"),
        **parse_name_group(elem),
        xml_id=xml_id(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_write_value_constraint(elem: etree._Element) -> Optional[WriteValueConstraint]:
    container = child(elem, "writeValueConstraint")
    if container is None:
        return None
    write_as_read_elem = child(container, "writeAsRead")
    use_enumerated_elem = child(container, "useEnumeratedValues")
    return WriteValueConstraint(
        write_as_read=as_bool(elem_text(write_as_read_elem)) if write_as_read_elem is not None else None,
        use_enumerated_values=as_bool(elem_text(use_enumerated_elem)) if use_enumerated_elem is not None else None,
        minimum=expr(container, "minimum"),
        maximum=expr(container, "maximum"),
    )


def _parse_access_restriction(elem: etree._Element) -> AccessRestriction:
    return AccessRestriction(
        mode_refs=parse_mode_refs(elem),
        read_access_mask=expr(elem, "readAccessMask"),
        write_access_mask=expr(elem, "writeAccessMask"),
        xml_id=xml_id(elem),
    )


def _parse_broadcast_to(elem: etree._Element) -> FieldReference:
    # broadcastTo is the only field-reference element with its own xml:id
    reference = parse_field_reference(elem)
    reference.xml_id = xml_id(elem)
    return reference


def _parse_field_access_policy(elem: etree._Element) -> FieldAccessPolicy:
    access = text(elem, "access")
    modified_write_value_elem = child(elem, "modifiedWriteValue")
    read_action_elem = child(elem, "readAction")
    testable_elem = child(elem, "testable")

    modified_write_value = elem_text(modified_write_value_elem)
    read_action = elem_text(read_action_elem)
    if testable_elem is not None:
        # testConstraint defaults to "unconstrained" when <testable> is present
        # without the attribute (memoryMap.xsd: testConstraint default="unconstrained").
        test_constraint = TestConstraint(testable_elem.get("testConstraint") or "unconstrained")
    else:
        test_constraint = None

    return FieldAccessPolicy(
        mode_refs=parse_mode_refs(elem),
        field_access_policy_definition_ref=parse_definition_ref(elem, "fieldAccessPolicyDefinitionRef"),
        access=AccessType(access) if access else None,
        modified_write_value=ModifiedWriteValue(modified_write_value) if modified_write_value else None,
        modified_write_value_modify=(
            modified_write_value_elem.get("modify") if modified_write_value_elem is not None else None
        ),
        write_value_constraint=_parse_write_value_constraint(elem),
        read_action=ReadAction(read_action) if read_action else None,
        read_action_modify=read_action_elem.get("modify") if read_action_elem is not None else None,
        read_response=expr(elem, "readResponse"),
        broadcast_to=parse_children(elem, "broadcasts", "broadcastTo", _parse_broadcast_to),
        access_restrictions=parse_children(elem, "accessRestrictions", "accessRestriction", _parse_access_restriction),
        testable=bool_text(elem, "testable"),
        test_constraint=test_constraint,
        reserved=expr(elem, "reserved"),
        xml_id=xml_id(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_field(elem: etree._Element) -> Field:
    enumerated_values_elem = child(elem, "enumeratedValues")
    field_access_policies_elem = child(elem, "fieldAccessPolicies")
    alias_of_elem = child(elem, "aliasOf")
    return Field(
        name=text(elem, "name") or "",
        bit_offset=required_expr(elem, "bitOffset"),
        bit_width=expr(elem, "bitWidth"),
        access_handles=parse_access_handles(elem),
        array=parse_memory_array(child(elem, "array")),
        field_definition_ref=parse_definition_ref(elem, "fieldDefinitionRef"),
        type_identifier=text(elem, "typeIdentifier"),
        volatile=bool_text(elem, "volatile"),
        resets=parse_children(elem, "resets", "reset", _parse_reset),
        alias_of=parse_field_reference(alias_of_elem) if alias_of_elem is not None else None,
        field_access_policies=parse_children(
            elem, "fieldAccessPolicies", "fieldAccessPolicy", _parse_field_access_policy
        ),
        field_access_policies_xml_id=xml_id(field_access_policies_elem),
        enumerated_values=parse_children(elem, "enumeratedValues", "enumeratedValue", _parse_enumerated_value),
        enumeration_definition_ref=(
            parse_definition_ref(enumerated_values_elem, "enumerationDefinitionRef")
            if enumerated_values_elem is not None
            else None
        ),
        **parse_name_group(elem),
        parameters=parse_parameters(elem),
        xml_id=xml_id(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_registers(elem: etree._Element) -> list:
    results = []
    for item_elem in elem:
        if item_elem.tag == qn("register"):
            results.append(_parse_register(item_elem))
        elif item_elem.tag == qn("registerFile"):
            results.append(_parse_register_file(item_elem))
    return results


def _parse_alternate_register(elem: etree._Element) -> AlternateRegister:
    return AlternateRegister(
        name=text(elem, "name") or "",
        access_handles=parse_access_handles(elem),
        mode_refs=parse_mode_refs(elem),
        type_identifier=text(elem, "typeIdentifier"),
        volatile=bool_text(elem, "volatile"),
        access_policies=_parse_access_policies(elem),
        fields=[_parse_field(f) for f in children(elem, "field")],
        **parse_name_group(elem),
        parameters=parse_parameters(elem),
        xml_id=xml_id(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_register(elem: etree._Element) -> Register:
    return Register(
        name=text(elem, "name") or "",
        address_offset=required_expr(elem, "addressOffset"),
        size=expr(elem, "size"),
        access_handles=parse_access_handles(elem),
        array=parse_memory_array(child(elem, "array")),
        register_definition_ref=parse_definition_ref(elem, "registerDefinitionRef"),
        type_identifier=text(elem, "typeIdentifier"),
        volatile=bool_text(elem, "volatile"),
        access_policies=_parse_access_policies(elem),
        fields=[_parse_field(f) for f in children(elem, "field")],
        alternate_registers=parse_children(
            elem, "alternateRegisters", "alternateRegister", _parse_alternate_register
        ),
        **parse_name_group(elem),
        parameters=parse_parameters(elem),
        xml_id=xml_id(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_register_file(elem: etree._Element) -> RegisterFile:
    return RegisterFile(
        name=text(elem, "name") or "",
        address_offset=required_expr(elem, "addressOffset"),
        range=expr(elem, "range"),
        access_handles=parse_access_handles(elem),
        array=parse_memory_array(child(elem, "array")),
        register_file_definition_ref=parse_definition_ref(elem, "registerFileDefinitionRef"),
        type_identifier=text(elem, "typeIdentifier"),
        access_policies=_parse_access_policies(elem),
        registers=_parse_registers(elem),
        **parse_name_group(elem),
        parameters=parse_parameters(elem),
        xml_id=xml_id(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_subspace_map(elem: etree._Element) -> SubspaceMap:
    return SubspaceMap(
        name=text(elem, "name") or "",
        initiator_ref=elem.get("initiatorRef", ""),
        base_address=expr(elem, "baseAddress"),
        segment_ref=elem.get("segmentRef"),
        **parse_name_group(elem),
        parameters=parse_parameters(elem),
        xml_id=xml_id(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_address_block(elem: etree._Element) -> AddressBlock:
    usage = text(elem, "usage")
    return AddressBlock(
        name=text(elem, "name") or "",
        range=expr(elem, "range"),
        width=expr(elem, "width"),
        base_address=expr(elem, "baseAddress"),
        access_handles=parse_access_handles(elem),
        array=parse_memory_array(child(elem, "array")),
        address_block_definition_ref=parse_definition_ref(elem, "addressBlockDefinitionRef"),
        type_identifier=text(elem, "typeIdentifier"),
        usage=UsageType(usage) if usage else None,
        volatile=bool_text(elem, "volatile"),
        access_policies=_parse_access_policies(elem),
        registers=_parse_registers(elem),
        misalignment_allowed=attr_bool(elem, "misalignmentAllowed", True),
        **parse_name_group(elem),
        parameters=parse_parameters(elem),
        xml_id=xml_id(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_memory_map_items(elem: etree._Element, allow_subspace: bool = True) -> list:
    items = []
    for item_elem in elem:
        if item_elem.tag == qn("addressBlock"):
            items.append(_parse_address_block(item_elem))
        elif item_elem.tag == qn("bank"):
            items.append(_parse_bank(item_elem))
        elif allow_subspace and item_elem.tag == qn("subspaceMap"):
            items.append(_parse_subspace_map(item_elem))
    return items


def _parse_bank(elem: etree._Element) -> Bank:
    usage = text(elem, "usage")
    return Bank(
        name=text(elem, "name") or "",
        bank_alignment=BankAlignment((elem.get("bankAlignment") or "").strip()),
        base_address=expr(elem, "baseAddress"),
        access_handles=parse_access_handles(elem),
        bank_definition_ref=parse_definition_ref(elem, "bankDefinitionRef"),
        items=_parse_memory_map_items(elem),
        usage=UsageType(usage) if usage else None,
        volatile=bool_text(elem, "volatile"),
        access_policies=_parse_access_policies(elem),
        parameters=parse_parameters(elem),
        **parse_name_group(elem),
        xml_id=xml_id(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_local_memory_map(elem: etree._Element) -> LocalMemoryMap:
    return LocalMemoryMap(
        name=text(elem, "name") or "",
        items=_parse_memory_map_items(elem, allow_subspace=False),
        **parse_name_group(elem),
        xml_id=xml_id(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_memory_remap(elem: etree._Element) -> MemoryRemap:
    return MemoryRemap(
        name=text(elem, "name") or "",
        mode_refs=parse_mode_refs(elem),
        remap_definition_ref=parse_definition_ref(elem, "remapDefinitionRef"),
        items=_parse_memory_map_items(elem),
        **parse_name_group(elem),
        xml_id=xml_id(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_memory_map(elem: etree._Element) -> MemoryMap:
    shared = text(elem, "shared")
    return MemoryMap(
        name=text(elem, "name") or "",
        memory_map_definition_ref=parse_definition_ref(elem, "memoryMapDefinitionRef"),
        items=_parse_memory_map_items(elem),
        memory_remaps=[_parse_memory_remap(e) for e in children(elem, "memoryRemap")],
        address_unit_bits=expr(elem, "addressUnitBits"),
        shared=SharedType(shared) if shared else None,
        **parse_name_group(elem),
        xml_id=xml_id(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_segment(elem: etree._Element) -> Segment:
    return Segment(
        name=text(elem, "name") or "",
        address_offset=required_expr(elem, "addressOffset"),
        range=required_expr(elem, "range"),
        **parse_name_group(elem),
        xml_id=xml_id(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_address_space(elem: etree._Element) -> AddressSpace:
    local_memory_map_elem = child(elem, "localMemoryMap")
    return AddressSpace(
        name=text(elem, "name") or "",
        range=required_expr(elem, "range"),
        width=required_expr(elem, "width"),
        segments=parse_children(elem, "segments", "segment", _parse_segment),
        address_unit_bits=expr(elem, "addressUnitBits"),
        local_memory_map=_parse_local_memory_map(local_memory_map_elem) if local_memory_map_elem is not None else None,
        **parse_name_group(elem),
        parameters=parse_parameters(elem),
        xml_id=xml_id(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


# --- ports / model ---


def _parse_clock_driver(elem: etree._Element) -> ClockDriver:
    period_elem = child(elem, "clockPeriod")
    offset_elem = child(elem, "clockPulseOffset")
    duration_elem = child(elem, "clockPulseDuration")
    return ClockDriver(
        clock_period=parse_optional_expression(period_elem) or Expression(""),
        clock_pulse_offset=parse_optional_expression(offset_elem) or Expression(""),
        clock_pulse_value=required_expr(elem, "clockPulseValue"),
        clock_pulse_duration=parse_optional_expression(duration_elem) or Expression(""),
        clock_name=elem.get("clockName"),
        period_units=period_elem.get("units", "ns") if period_elem is not None else "ns",
        offset_units=offset_elem.get("units", "ns") if offset_elem is not None else "ns",
        duration_units=duration_elem.get("units", "ns") if duration_elem is not None else "ns",
        xml_id=xml_id(elem),
    )


def _parse_single_shot_driver(elem: etree._Element) -> SingleShotDriver:
    offset_elem = child(elem, "singleShotOffset")
    duration_elem = child(elem, "singleShotDuration")
    return SingleShotDriver(
        single_shot_offset=parse_optional_expression(offset_elem) or Expression(""),
        single_shot_value=required_expr(elem, "singleShotValue"),
        single_shot_duration=parse_optional_expression(duration_elem) or Expression(""),
        offset_units=offset_elem.get("units", "ns") if offset_elem is not None else "ns",
        duration_units=duration_elem.get("units", "ns") if duration_elem is not None else "ns",
    )


def _parse_driver(elem: etree._Element) -> Driver:
    clock_driver_elem = child(elem, "clockDriver")
    single_shot_elem = child(elem, "singleShotDriver")
    return Driver(
        default_value=expr(elem, "defaultValue"),
        clock_driver=_parse_clock_driver(clock_driver_elem) if clock_driver_elem is not None else None,
        single_shot_driver=_parse_single_shot_driver(single_shot_elem) if single_shot_elem is not None else None,
        range=parse_range(elem),
        view_refs=text_values(elem, "viewRef"),
        xml_id=xml_id(elem),
    )


def _parse_constraint_set(elem: etree._Element) -> ConstraintSet:
    vector_elem = child(elem, "vector")
    return ConstraintSet(
        name=text(elem, "name"),
        vector=parse_vector(vector_elem) if vector_elem is not None else None,
        drive_constraint=parse_drive_constraint(elem),
        load_constraint=parse_load_constraint(elem),
        timing_constraints=parse_timing_constraints(elem),
        constraint_set_id=elem.get("constraintSetId", "default"),
        **parse_name_group(elem),
        xml_id=xml_id(elem),
    )


def _parse_wire_type_def(elem: etree._Element) -> WireTypeDef:
    type_name_elem = child(elem, "typeName")
    constrained = type_name_elem.get("constrained") if type_name_elem is not None else None
    return WireTypeDef(
        type_name=elem_text(type_name_elem),
        type_name_constrained=constrained.split() if constrained else [],
        type_definitions=text_values(elem, "typeDefinition"),
        view_refs=text_values(elem, "viewRef"),
        xml_id=xml_id(elem),
    )


def _parse_domain_type_def(elem: etree._Element) -> DomainTypeDef:
    type_name_elem = child(elem, "typeName")
    return DomainTypeDef(
        type_name=text_value(type_name_elem) if type_name_elem is not None else None,
        type_definitions=text_values(elem, "typeDefinition"),
        view_refs=text_values(elem, "viewRef"),
        xml_id=xml_id(elem),
    )


def _parse_signal_type_def(elem: etree._Element) -> SignalTypeDef:
    return SignalTypeDef(
        signal_type=text(elem, "signalType") or "", view_refs=text_values(elem, "viewRef"), xml_id=xml_id(elem)
    )


def _parse_power_constraint(elem: etree._Element) -> PowerConstraint:
    return PowerConstraint(
        power_domain_ref=text(elem, "powerDomainRef") or "",
        range=parse_range(elem),
        xml_id=xml_id(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_wire_port(elem: etree._Element) -> WirePort:
    direction = elem_text(child(elem, "direction"))
    return WirePort(
        direction=Direction(direction) if direction else Direction.IN,
        qualifier=parse_qualifier(elem),
        vectors=parse_vectors(elem),
        wire_type_defs=parse_children(elem, "wireTypeDefs", "wireTypeDef", _parse_wire_type_def),
        domain_type_defs=parse_children(elem, "domainTypeDefs", "domainTypeDef", _parse_domain_type_def),
        signal_type_defs=parse_children(elem, "signalTypeDefs", "signalTypeDef", _parse_signal_type_def),
        drivers=parse_children(elem, "drivers", "driver", _parse_driver),
        constraint_sets=parse_children(elem, "constraintSets", "constraintSet", _parse_constraint_set),
        power_constraints=parse_children(elem, "powerConstraints", "powerConstraint", _parse_power_constraint),
        all_logical_directions_allowed=attr_bool(elem, "allLogicalDirectionsAllowed", False),
    )


def _parse_type_parameters(elem: etree._Element) -> tuple[list[ModuleParameter], list[ServiceTypeDef]]:
    """ipxact:typeParameters - typeParameter elements, plus serviceTypeDef elements where allowed."""
    container = child(elem, "typeParameters")
    if container is None:
        return [], []
    return (
        [_parse_module_parameter(p) for p in children(container, "typeParameter")],
        [_parse_service_type_def(s) for s in children(container, "serviceTypeDef")],
    )


def _parse_service_type_def(elem: etree._Element) -> ServiceTypeDef:
    type_name_elem = child(elem, "typeName")
    type_parameters, service_type_defs = _parse_type_parameters(elem)
    return ServiceTypeDef(
        type_name=elem_text(type_name_elem) or "",
        type_name_implicit=attr_bool(type_name_elem, "implicit", False) if type_name_elem is not None else False,
        type_definitions=text_values(elem, "typeDefinition"),
        type_parameters=type_parameters,
        service_type_defs=service_type_defs,
        xml_id=xml_id(elem),
    )


def _parse_trans_type_def(elem: etree._Element) -> TransTypeDef:
    type_name_elem = child(elem, "typeName")
    type_parameters, service_type_defs = _parse_type_parameters(elem)
    return TransTypeDef(
        type_name=elem_text(type_name_elem),
        type_name_exact=attr_bool(type_name_elem, "exact", True) if type_name_elem is not None else True,
        type_definitions=text_values(elem, "typeDefinition"),
        type_parameters=type_parameters,
        service_type_defs=service_type_defs,
        view_refs=text_values(elem, "viewRef"),
        xml_id=xml_id(elem),
    )


def _parse_transactional_port(elem: etree._Element) -> TransactionalPort:
    initiative = elem_text(child(elem, "initiative"))
    kind_elem = child(elem, "kind")
    connection_elem = child(elem, "connection")
    return TransactionalPort(
        initiative=Initiative(initiative) if initiative else Initiative.REQUIRES,
        kind=elem_text(kind_elem),
        kind_custom=kind_elem.get("custom") if kind_elem is not None else None,
        bus_width=expr(elem, "busWidth"),
        qualifier=parse_qualifier(elem),
        protocol=parse_protocol(elem),
        trans_type_defs=parse_children(elem, "transTypeDefs", "transTypeDef", _parse_trans_type_def),
        max_connections=expr(connection_elem, "maxConnections"),
        min_connections=expr(connection_elem, "minConnections"),
        power_constraints=parse_children(elem, "powerConstraints", "powerConstraint", _parse_power_constraint),
        all_logical_initiatives_allowed=attr_bool(elem, "allLogicalInitiativesAllowed", False),
    )


def _parse_port_access(elem: etree._Element) -> Optional[PortAccess]:
    access_elem = child(elem, "access")
    if access_elem is None:
        return None
    return PortAccess(
        port_access_type=text(access_elem, "portAccessType"), access_handles=parse_access_handles(access_elem)
    )


def _struct_type_of(elem: etree._Element) -> str:
    for candidate in ("struct", "union", "interface"):
        if child(elem, candidate) is not None:
            return candidate
    return "struct"


def _parse_sub_port(elem: etree._Element) -> SubPort:
    wire_elem = child(elem, "wire")
    structured_elem = child(elem, "structured")
    return SubPort(
        name=text(elem, "name") or "",
        wire=_parse_wire_port(wire_elem) if wire_elem is not None else None,
        structured=_parse_structured_port(structured_elem) if structured_elem is not None else None,
        arrays=parse_array_bounds(elem),
        access=_parse_port_access(elem),
        **parse_name_group(elem),
        is_io=as_bool(elem.get("isIO")),
        xml_id=xml_id(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_struct_port_type_def(elem: etree._Element) -> StructPortTypeDef:
    type_name_elem = child(elem, "typeName")
    constrained = type_name_elem.get("constrained") if type_name_elem is not None else None
    return StructPortTypeDef(
        type_name=(elem_text(type_name_elem) or "") if type_name_elem is not None else "",
        constrained=constrained.split() if constrained else [],
        type_definitions=text_values(elem, "typeDefinition"),
        type_parameters=parse_children(elem, "typeParameters", "typeParameter", _parse_module_parameter),
        role=text(elem, "role"),
        view_refs=text_values(elem, "viewRef"),
        xml_id=xml_id(elem),
    )


def _parse_structured_port(elem: etree._Element) -> StructuredPort:
    struct_type = _struct_type_of(elem)
    struct_type_elem = child(elem, struct_type)
    direction = None
    phantom = None
    if struct_type_elem is not None:
        if struct_type in ("struct", "union"):
            direction_value = struct_type_elem.get("direction")
            direction = Direction(direction_value) if direction_value else None
        else:
            phantom = as_bool(struct_type_elem.get("phantom"))
    return StructuredPort(
        struct_type=struct_type,
        vectors=parse_vectors(elem),
        sub_ports=parse_children(elem, "subPorts", "subPort", _parse_sub_port),
        packed=attr_bool(elem, "packed", True),
        direction=direction,
        phantom=phantom,
        struct_port_type_defs=parse_children(
            elem, "structPortTypeDefs", "structPortTypeDef", _parse_struct_port_type_def
        ),
    )


def _parse_field_map(elem: etree._Element) -> FieldMap:
    return FieldMap(
        field_slice=parse_field_reference(child(elem, "fieldSlice")),
        sub_port_refs=parse_sub_port_references(elem),
        part_select=parse_part_select(elem),
        mode_refs=parse_mode_refs(elem),
        xml_id=xml_id(elem),
    )


def _parse_port(elem: etree._Element) -> Port:
    wire_elem = child(elem, "wire")
    transactional_elem = child(elem, "transactional")
    structured_elem = child(elem, "structured")
    return Port(
        name=text(elem, "name") or "",
        wire=_parse_wire_port(wire_elem) if wire_elem is not None else None,
        transactional=_parse_transactional_port(transactional_elem) if transactional_elem is not None else None,
        structured=_parse_structured_port(structured_elem) if structured_elem is not None else None,
        field_maps=parse_children(elem, "fieldMaps", "fieldMap", _parse_field_map),
        arrays=parse_array_bounds(elem),
        access=_parse_port_access(elem),
        **parse_name_group(elem),
        parameters=parse_parameters(elem),
        xml_id=xml_id(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_view(elem: etree._Element) -> View:
    return View(
        name=text(elem, "name") or "",
        env_identifiers=text_values(elem, "envIdentifier"),
        component_instantiation_ref=text(elem, "componentInstantiationRef"),
        design_instantiation_ref=text(elem, "designInstantiationRef"),
        design_configuration_instantiation_ref=text(elem, "designConfigurationInstantiationRef"),
        **parse_name_group(elem),
        xml_id=xml_id(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_module_parameter(elem: etree._Element) -> ModuleParameter:
    constrained = elem.get("constrained")
    return ModuleParameter(
        **parse_parameter_fields(elem),
        data_type=elem.get("dataType"),
        usage_type=elem.get("usageType", "typed"),
        data_type_definition=elem.get("dataTypeDefinition"),
        constrained=constrained.split() if constrained else [],
    )


def _parse_clearbox_element_ref(elem: etree._Element) -> ClearboxElementRef:
    return ClearboxElementRef(
        name=elem.get("name", ""),
        locations=[parse_location(loc) for loc in children(elem, "location")],
        xml_id=xml_id(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_language(elem: etree._Element) -> tuple[Optional[str], bool]:
    """ipxact:language text and its strict attribute."""
    language_elem = child(elem, "language")
    if language_elem is None:
        return None, False
    return elem_text(language_elem), attr_bool(language_elem, "strict", False)


def _parse_component_instantiation(elem: etree._Element) -> ComponentInstantiation:
    language, language_strict = _parse_language(elem)
    return ComponentInstantiation(
        name=text(elem, "name") or "",
        is_virtual=bool_text(elem, "isVirtual", False),
        language=language,
        language_strict=language_strict,
        library_name=text(elem, "libraryName"),
        package_name=text(elem, "packageName"),
        module_name=text(elem, "moduleName"),
        architecture_name=text(elem, "architectureName"),
        configuration_name=text(elem, "configurationName"),
        module_parameters=parse_children(elem, "moduleParameters", "moduleParameter", _parse_module_parameter),
        default_file_builders=[parse_file_builder(b) for b in children(elem, "defaultFileBuilder")],
        file_set_refs=[parse_local_reference(r) for r in children(elem, "fileSetRef")],
        constraint_set_refs=[parse_local_reference(r) for r in children(elem, "constraintSetRef")],
        clearbox_element_refs=parse_children(
            elem, "clearboxElementRefs", "clearboxElementRef", _parse_clearbox_element_ref
        ),
        parameters=parse_parameters(elem),
        **parse_name_group(elem),
        xml_id=xml_id(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_design_instantiation(elem: etree._Element) -> DesignInstantiation:
    return DesignInstantiation(
        name=text(elem, "name") or "",
        design_ref=parse_vlnv_ref(child(elem, "designRef")),
        **parse_name_group(elem),
        xml_id=xml_id(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_design_configuration_instantiation(elem: etree._Element) -> DesignConfigurationInstantiation:
    language, language_strict = _parse_language(elem)
    return DesignConfigurationInstantiation(
        name=text(elem, "name") or "",
        design_configuration_ref=parse_vlnv_ref(child(elem, "designConfigurationRef")),
        language=language,
        language_strict=language_strict,
        parameters=parse_parameters(elem),
        **parse_name_group(elem),
        xml_id=xml_id(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_model(elem: etree._Element) -> Model:
    views = parse_children(elem, "views", "view", _parse_view)

    component_instantiations = []
    design_instantiations = []
    design_configuration_instantiations = []
    instantiations_container = child(elem, "instantiations")
    if instantiations_container is not None:
        for instantiation_elem in instantiations_container:
            if instantiation_elem.tag == qn("componentInstantiation"):
                component_instantiations.append(_parse_component_instantiation(instantiation_elem))
            elif instantiation_elem.tag == qn("designInstantiation"):
                design_instantiations.append(_parse_design_instantiation(instantiation_elem))
            elif instantiation_elem.tag == qn("designConfigurationInstantiation"):
                design_configuration_instantiations.append(
                    _parse_design_configuration_instantiation(instantiation_elem)
                )

    ports = parse_children(elem, "ports", "port", _parse_port)

    return Model(
        views=views,
        component_instantiations=component_instantiations,
        design_instantiations=design_instantiations,
        design_configuration_instantiations=design_configuration_instantiations,
        ports=ports,
    )


# --- remaining component-level sections ---


def _parse_cpu_region(elem: etree._Element) -> CpuRegion:
    return CpuRegion(
        name=text(elem, "name") or "",
        address_offset=required_expr(elem, "addressOffset"),
        range=required_expr(elem, "range"),
        **parse_name_group(elem),
        xml_id=xml_id(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_linker_command_file(elem: etree._Element) -> LinkerCommandFile:
    return LinkerCommandFile(
        name=required_expr(elem, "name"),
        command_line_switch=required_expr(elem, "commandLineSwitch"),
        enable=required_expr(elem, "enable"),
        generator_refs=text_values(elem, "generatorRef"),
        xml_id=xml_id(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_language_tools(elem: Optional[etree._Element]) -> Optional[LanguageTools]:
    if elem is None:
        return None
    linker_command_file_elem = child(elem, "linkerCommandFile")
    return LanguageTools(
        file_builders=[parse_file_builder(b) for b in children(elem, "fileBuilder")],
        linker=expr(elem, "linker"),
        linker_flags=expr(elem, "linkerFlags"),
        linker_command_file=(
            _parse_linker_command_file(linker_command_file_elem) if linker_command_file_elem is not None else None
        ),
    )


def _parse_executable_image(elem: etree._Element) -> ExecutableImage:
    file_set_ref_group_elem = child(elem, "fileSetRefGroup")
    return ExecutableImage(
        name=text(elem, "name") or "",
        image_id=elem.get("imageId", ""),
        image_type=elem.get("imageType"),
        parameters=parse_parameters(elem),
        language_tools=_parse_language_tools(child(elem, "languageTools")),
        file_set_ref_group=(
            parse_file_set_ref_group(file_set_ref_group_elem) if file_set_ref_group_elem is not None else None
        ),
        **parse_name_group(elem),
        xml_id=xml_id(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_cpu(elem: etree._Element) -> Cpu:
    return Cpu(
        name=text(elem, "name") or "",
        range=required_expr(elem, "range"),
        width=required_expr(elem, "width"),
        memory_map_ref=text(elem, "memoryMapRef") or "",
        regions=parse_children(elem, "regions", "region", _parse_cpu_region),
        address_unit_bits=expr(elem, "addressUnitBits"),
        executable_images=[_parse_executable_image(e) for e in children(elem, "executableImage")],
        parameters=parse_parameters(elem),
        **parse_name_group(elem),
        xml_id=xml_id(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_power_domain(elem: etree._Element) -> PowerDomain:
    return PowerDomain(
        name=text(elem, "name") or "",
        always_on=expr(elem, "alwaysOn"),
        sub_domain_of=text(elem, "subDomainOf"),
        parameters=parse_parameters(elem),
        **parse_name_group(elem),
        xml_id=xml_id(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_clearbox_element(elem: etree._Element) -> ClearboxElement:
    return ClearboxElement(
        name=text(elem, "name") or "",
        clearbox_type=text(elem, "clearboxType") or "",
        driveable=bool_text(elem, "driveable", False),
        parameters=parse_parameters(elem),
        **parse_name_group(elem),
        xml_id=xml_id(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_component_generator(elem: etree._Element) -> ComponentGenerator:
    api_type_elem = child(elem, "apiType")
    transport_methods_elem = child(elem, "transportMethods")
    return ComponentGenerator(
        name=text(elem, "name") or "",
        generator_exe=text(elem, "generatorExe") or "",
        phase=expr(elem, "phase"),
        parameters=parse_parameters(elem),
        api_type=text_value(api_type_elem) if api_type_elem is not None else None,
        api_service=text(elem, "apiService") or "SOAP",
        transport_methods=(
            text_values(transport_methods_elem, "transportMethod") if transport_methods_elem is not None else []
        ),
        transport_methods_xml_id=xml_id(transport_methods_elem),
        groups=text_values(elem, "group"),
        scope=elem.get("scope", "instance"),
        hidden=attr_bool(elem, "hidden", False),
        **parse_name_group(elem),
        xml_id=xml_id(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_reset_type(elem: etree._Element) -> ResetType:
    return ResetType(
        name=text(elem, "name") or "",
        **parse_name_group(elem),
        xml_id=xml_id(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_other_clock_driver(elem: etree._Element) -> OtherClockDriver:
    base = _parse_clock_driver(elem)
    return OtherClockDriver(
        clock_name=elem.get("clockName", ""),
        clock_period=base.clock_period,
        clock_pulse_offset=base.clock_pulse_offset,
        clock_pulse_value=base.clock_pulse_value,
        clock_pulse_duration=base.clock_pulse_duration,
        clock_source=elem.get("clockSource"),
        period_units=base.period_units,
        offset_units=base.offset_units,
        duration_units=base.duration_units,
        xml_id=xml_id(elem),
    )


def _parse_link_refs(elem: etree._Element, external_tag: str, internal_tag: str, attribute: str) -> tuple[str, str]:
    """The two attribute-only references of a viewLink/modeLink/resetTypeLink."""
    external_elem = child(elem, external_tag)
    internal_elem = child(elem, internal_tag)
    return (
        external_elem.get(attribute, "") if external_elem is not None else "",
        internal_elem.get(attribute, "") if internal_elem is not None else "",
    )


def _parse_view_link(elem: etree._Element) -> ViewLink:
    external, internal = _parse_link_refs(elem, "externalViewReference", "viewReference", "viewRef")
    return ViewLink(
        external_view_ref=external,
        view_ref=internal,
        xml_id=xml_id(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_mode_link(elem: etree._Element) -> ModeLink:
    external, internal = _parse_link_refs(elem, "externalModeReference", "modeReference", "modeRef")
    return ModeLink(
        external_mode_ref=external,
        mode_ref=internal,
        xml_id=xml_id(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_reset_type_link(elem: etree._Element) -> ResetTypeLink:
    external, internal = _parse_link_refs(elem, "externalResetTypeReference", "resetTypeReference", "resetTypeRef")
    return ResetTypeLink(
        external_reset_type_ref=external,
        reset_type_ref=internal,
        xml_id=xml_id(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_external_type_definitions_ref(elem: etree._Element) -> ExternalTypeDefinitionsRef:
    ref_elem = child(elem, "typeDefinitionsRef")
    return ExternalTypeDefinitionsRef(
        type_definitions=parse_vlnv_ref(ref_elem) if ref_elem is not None else VLNVRef("", "", "", ""),
        name=text(elem, "name"),
        view_links=parse_children(elem, "viewLinks", "viewLink", _parse_view_link),
        mode_links=parse_children(elem, "modeLinks", "modeLink", _parse_mode_link),
        reset_type_links=parse_children(elem, "resetTypeLinks", "resetTypeLink", _parse_reset_type_link),
        **parse_name_group(elem),
        xml_id=xml_id(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )
