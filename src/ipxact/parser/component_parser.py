from __future__ import annotations

from typing import Optional

from lxml import etree

from ..schema.businterface import (
    AbstractionType,
    BusInterface,
    Channel,
    FieldReference,
    FileSetRefGroup,
    IndirectInterface,
    InitiatorInterface,
    InterfaceMode,
    MirroredTargetInterface,
    MonitorInterface,
    PortMap,
    RemapAddress,
    SystemInterface,
    TargetInterface,
    TransparentBridge,
)
from ..schema.common import ArrayDim, MemoryArray, ModuleParameter, PartSelect
from ..schema.component import Component
from ..schema.component_sections import (
    ClearboxElement,
    ComponentGenerator,
    Cpu,
    CpuRegion,
    ExternalTypeDefinitionsRef,
    FieldSlice,
    Mode,
    OtherClockDriver,
    PortSlice,
    PowerDomain,
    ResetType,
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
    ComponentInstantiation,
    DesignConfigurationInstantiation,
    DesignInstantiation,
    FileBuilderOverride,
    Model,
    View,
)
from ..schema.ports import (
    ClockDriver,
    ConstraintSet,
    Direction,
    Driver,
    FieldMap,
    Initiative,
    Port,
    SingleShotDriver,
    StructuredPort,
    SubPort,
    TransactionalPort,
    WirePort,
)
from ..schema.vlnv import VLNVRef
from .common_parser import (
    as_bool,
    attr_bool,
    bool_text,
    child,
    children,
    elem_text,
    parse_assertions,
    parse_children,
    parse_choices,
    parse_drive_constraint,
    parse_file_sets,
    parse_load_constraint,
    parse_mode_refs,
    parse_parameter,
    parse_parameters,
    parse_part_select,
    parse_protocol,
    parse_qualifier,
    parse_sub_port_references,
    parse_texts,
    parse_timing_constraints,
    parse_vectors,
    parse_vendor_extensions,
    parse_vlnv,
    parse_vlnv_ref,
    qn,
    text,
    texts,
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
        display_name=text(root, "displayName"),
        short_description=text(root, "shortDescription"),
        description=text(root, "description"),
        vendor_extensions=parse_vendor_extensions(root),
    )


# --- bus interfaces ---


def _parse_port_map(elem: etree._Element) -> PortMap:
    logical_port_elem = child(elem, "logicalPort")
    physical_port_elem = child(elem, "physicalPort")
    return PortMap(
        logical_port=text(logical_port_elem, "name") or "" if logical_port_elem is not None else "",
        physical_port=text(physical_port_elem, "name") if physical_port_elem is not None else None,
        logical_tie_off=text(elem, "logicalTieOff"),
        invert=attr_bool(elem, "invert", False),
        is_informative=bool_text(elem, "isInformative", False),
    )


def _parse_abstraction_type(elem: etree._Element) -> AbstractionType:
    return AbstractionType(
        abstraction_ref=parse_vlnv_ref(child(elem, "abstractionRef")),
        port_maps=parse_children(elem, "portMaps", "portMap", _parse_port_map),
        view_refs=texts(elem, "viewRef"),
    )


def _parse_file_set_refs(elem: etree._Element, tag: str = "fileSetRef") -> list[str]:
    refs = []
    for ref_elem in children(elem, tag):
        local_name = text(ref_elem, "localName")
        if local_name is not None:
            refs.append(local_name)
    return refs


def _parse_constraint_set_refs(elem: etree._Element) -> list[str]:
    return _parse_file_set_refs(elem, tag="constraintSetRef")


def _parse_initiator_interface(elem: etree._Element) -> InitiatorInterface:
    address_space_ref_elem = child(elem, "addressSpaceRef")
    if address_space_ref_elem is None:
        return InitiatorInterface()
    return InitiatorInterface(
        address_space_ref=address_space_ref_elem.get("addressSpaceRef"),
        base_address=text(address_space_ref_elem, "baseAddress"),
        mode_refs=parse_mode_refs(address_space_ref_elem),
    )


def _parse_target_interface(elem: etree._Element) -> TargetInterface:
    memory_map_ref_elem = child(elem, "memoryMapRef")
    return TargetInterface(
        memory_map_ref=memory_map_ref_elem.get("memoryMapRef") if memory_map_ref_elem is not None else None,
        mode_refs=parse_mode_refs(memory_map_ref_elem) if memory_map_ref_elem is not None else [],
        transparent_bridges=[
            TransparentBridge(initiator_ref=b.get("initiatorRef", "")) for b in children(elem, "transparentBridge")
        ],
        file_set_ref_groups=[
            FileSetRefGroup(group=text(g, "group"), file_set_refs=_parse_file_set_refs(g))
            for g in children(elem, "fileSetRefGroup")
        ],
    )


def _parse_mirrored_target_interface(elem: etree._Element) -> MirroredTargetInterface:
    base_addresses_elem = child(elem, "baseAddresses")
    if base_addresses_elem is None:
        return MirroredTargetInterface()
    remap_addresses = []
    for remap_addresses_elem in children(base_addresses_elem, "remapAddresses"):
        remap_address_elem = child(remap_addresses_elem, "remapAddress")
        remap_addresses.append(
            RemapAddress(
                value=elem_text(remap_address_elem) or "",
                mode_refs=parse_mode_refs(remap_addresses_elem),
            )
        )
    return MirroredTargetInterface(remap_addresses=remap_addresses, range=text(base_addresses_elem, "range"))


def _parse_bus_interface(elem: etree._Element) -> BusInterface:
    mode = InterfaceMode.MIRRORED_INITIATOR
    initiator = target = mirrored_target = monitor = None
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
    elif child(elem, "mirroredInitiator") is not None:
        mode = InterfaceMode.MIRRORED_INITIATOR
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
        mirrored_system=mirrored_system,
        monitor=monitor,
        connection_required=bool_text(elem, "connectionRequired", False),
        bits_in_lau=text(elem, "bitsInLau"),
        # bitSteering defaults to "0" when absent
        bit_steering=text(elem, "bitSteering") or "0",
        endianness=text(elem, "endianness"),
        parameters=parse_parameters(elem),
        display_name=text(elem, "displayName"),
        description=text(elem, "description"),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_range(elem: Optional[etree._Element]) -> Optional[PartSelect]:
    if elem is None:
        return None
    return PartSelect(range_left=text(elem, "left"), range_right=text(elem, "right"))


def _parse_field_reference(elem: etree._Element) -> FieldReference:
    address_space_ref_elem = child(elem, "addressSpaceRef")
    memory_map_ref_elem = child(elem, "memoryMapRef")
    memory_remap_ref_elem = child(elem, "memoryRemapRef")
    address_block_ref_elem = child(elem, "addressBlockRef")
    register_ref_elem = child(elem, "registerRef")
    alternate_register_ref_elem = child(elem, "alternateRegisterRef")
    field_ref_elem = child(elem, "fieldRef")

    return FieldReference(
        field_ref=field_ref_elem.get("fieldRef", "") if field_ref_elem is not None else "",
        register_ref=register_ref_elem.get("registerRef") if register_ref_elem is not None else None,
        alternate_register_ref=(
            alternate_register_ref_elem.get("alternateRegisterRef")
            if alternate_register_ref_elem is not None
            else None
        ),
        register_file_refs=[e.get("registerFileRef", "") for e in children(elem, "registerFileRef")],
        address_block_ref=address_block_ref_elem.get("addressBlockRef") if address_block_ref_elem is not None else None,
        bank_refs=[e.get("bankRef", "") for e in children(elem, "bankRef")],
        memory_map_ref=memory_map_ref_elem.get("memoryMapRef") if memory_map_ref_elem is not None else None,
        memory_remap_ref=memory_remap_ref_elem.get("memoryRemapRef") if memory_remap_ref_elem is not None else None,
        address_space_ref=address_space_ref_elem.get("addressSpaceRef") if address_space_ref_elem is not None else None,
        range=_parse_range(child(elem, "range")),
    )


def _parse_indirect_interface(elem: etree._Element) -> IndirectInterface:
    memory_map_ref_elem = child(elem, "memoryMapRef")
    return IndirectInterface(
        name=text(elem, "name") or "",
        indirect_address_ref=_parse_field_reference(child(elem, "indirectAddressRef")),
        indirect_data_ref=_parse_field_reference(child(elem, "indirectDataRef")),
        memory_map_ref=elem_text(memory_map_ref_elem),
        transparent_bridges=[
            TransparentBridge(initiator_ref=b.get("initiatorRef", "")) for b in children(elem, "transparentBridge")
        ],
        bits_in_lau=text(elem, "bitsInLau"),
        endianness=text(elem, "endianness"),
        display_name=text(elem, "displayName"),
        description=text(elem, "description"),
        parameters=parse_parameters(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_channel(elem: etree._Element) -> Channel:
    return Channel(
        name=text(elem, "name") or "",
        bus_interface_refs=_parse_file_set_refs(elem, tag="busInterfaceRef"),
        display_name=text(elem, "displayName"),
        description=text(elem, "description"),
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
        display_name=text(elem, "displayName"),
        description=text(elem, "description"),
    )


def _parse_field_slice(elem: etree._Element) -> FieldSlice:
    return FieldSlice(
        name=text(elem, "name") or "",
        field_ref=_parse_field_reference(elem),
        display_name=text(elem, "displayName"),
        description=text(elem, "description"),
    )


def _parse_mode(elem: etree._Element) -> Mode:
    return Mode(
        name=text(elem, "name") or "",
        port_slices=[_parse_port_slice(e) for e in children(elem, "portSlice")],
        field_slices=[_parse_field_slice(e) for e in children(elem, "fieldSlice")],
        condition=text(elem, "condition"),
        vendor_extensions=parse_vendor_extensions(elem),
    )


# --- memory maps ---


def _parse_memory_array(elem: Optional[etree._Element]) -> Optional[MemoryArray]:
    if elem is None:
        return None
    dims = [ArrayDim(size=elem_text(d) or "", index_var=d.get("indexVar")) for d in children(elem, "dim")]
    stride_elem = child(elem, "stride") or child(elem, "bitStride")
    return MemoryArray(dims=dims, stride=elem_text(stride_elem))


def _parse_access_policy(elem: etree._Element) -> AccessPolicy:
    access = text(elem, "access")
    return AccessPolicy(mode_refs=parse_mode_refs(elem), access=AccessType(access) if access else None)


def _parse_access_policies(elem: etree._Element) -> list[AccessPolicy]:
    return parse_children(elem, "accessPolicies", "accessPolicy", _parse_access_policy)


def _parse_reset(elem: etree._Element) -> Reset:
    return Reset(value=text(elem, "value") or "", mask=text(elem, "mask"), reset_type_ref=elem.get("resetTypeRef"))


def _parse_enumerated_value(elem: etree._Element) -> EnumeratedValue:
    return EnumeratedValue(
        name=text(elem, "name") or "",
        value=text(elem, "value") or "",
        usage=elem.get("usage", "read-write"),
        display_name=text(elem, "displayName"),
        description=text(elem, "description"),
    )


def _parse_write_value_constraint(elem: etree._Element) -> Optional[WriteValueConstraint]:
    container = child(elem, "writeValueConstraint")
    if container is None:
        return None
    write_as_read_elem = child(container, "writeAsRead")
    use_enumerated_elem = child(container, "useEnumeratedValues")
    return WriteValueConstraint(
        write_as_read=as_bool(write_as_read_elem.text) if write_as_read_elem is not None else None,
        use_enumerated_values=as_bool(use_enumerated_elem.text) if use_enumerated_elem is not None else None,
        minimum=text(container, "minimum"),
        maximum=text(container, "maximum"),
    )


def _parse_access_restriction(elem: etree._Element) -> AccessRestriction:
    return AccessRestriction(
        mode_refs=parse_mode_refs(elem),
        read_access_mask=text(elem, "readAccessMask"),
        write_access_mask=text(elem, "writeAccessMask"),
    )


def _parse_field_access_policy(elem: etree._Element) -> FieldAccessPolicy:
    access = text(elem, "access")
    modified_write_value_elem = child(elem, "modifiedWriteValue")
    read_action_elem = child(elem, "readAction")
    testable_elem = child(elem, "testable")
    broadcasts_container = child(elem, "broadcasts")
    broadcast_to = []
    if broadcasts_container is not None:
        for broadcast_elem in children(broadcasts_container, "broadcastTo"):
            field_ref_elem = child(broadcast_elem, "fieldRef")
            if field_ref_elem is not None:
                broadcast_to.append(field_ref_elem.get("fieldRef", ""))

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
        access=AccessType(access) if access else None,
        modified_write_value=ModifiedWriteValue(modified_write_value) if modified_write_value else None,
        write_value_constraint=_parse_write_value_constraint(elem),
        read_action=ReadAction(read_action) if read_action else None,
        read_response=text(elem, "readResponse"),
        broadcast_to=broadcast_to,
        access_restrictions=parse_children(elem, "accessRestrictions", "accessRestriction", _parse_access_restriction),
        testable=bool_text(elem, "testable"),
        test_constraint=test_constraint,
        reserved=text(elem, "reserved"),
    )


def _parse_field(elem: etree._Element) -> Field:
    return Field(
        name=text(elem, "name") or "",
        bit_offset=text(elem, "bitOffset") or "",
        bit_width=text(elem, "bitWidth") or "",
        array=_parse_memory_array(child(elem, "array")),
        volatile=bool_text(elem, "volatile"),
        resets=parse_children(elem, "resets", "reset", _parse_reset),
        field_access_policies=parse_children(
            elem, "fieldAccessPolicies", "fieldAccessPolicy", _parse_field_access_policy
        ),
        enumerated_values=parse_children(elem, "enumeratedValues", "enumeratedValue", _parse_enumerated_value),
        display_name=text(elem, "displayName"),
        description=text(elem, "description"),
        parameters=parse_parameters(elem),
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
        mode_refs=parse_mode_refs(elem),
        volatile=bool_text(elem, "volatile"),
        access_policies=_parse_access_policies(elem),
        fields=[_parse_field(f) for f in children(elem, "field")],
        display_name=text(elem, "displayName"),
        description=text(elem, "description"),
        parameters=parse_parameters(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_register(elem: etree._Element) -> Register:
    return Register(
        name=text(elem, "name") or "",
        address_offset=text(elem, "addressOffset") or "",
        size=text(elem, "size") or "",
        array=_parse_memory_array(child(elem, "array")),
        volatile=bool_text(elem, "volatile"),
        access_policies=_parse_access_policies(elem),
        fields=[_parse_field(f) for f in children(elem, "field")],
        alternate_registers=parse_children(
            elem, "alternateRegisters", "alternateRegister", _parse_alternate_register
        ),
        display_name=text(elem, "displayName"),
        description=text(elem, "description"),
        parameters=parse_parameters(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_register_file(elem: etree._Element) -> RegisterFile:
    return RegisterFile(
        name=text(elem, "name") or "",
        address_offset=text(elem, "addressOffset") or "",
        range=text(elem, "range") or "",
        array=_parse_memory_array(child(elem, "array")),
        access_policies=_parse_access_policies(elem),
        registers=_parse_registers(elem),
        display_name=text(elem, "displayName"),
        description=text(elem, "description"),
        parameters=parse_parameters(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_subspace_map(elem: etree._Element) -> SubspaceMap:
    return SubspaceMap(
        name=text(elem, "name") or "",
        initiator_ref=elem.get("initiatorRef", ""),
        base_address=text(elem, "baseAddress"),
        segment_ref=elem.get("segmentRef"),
        display_name=text(elem, "displayName"),
        description=text(elem, "description"),
        parameters=parse_parameters(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_address_block(elem: etree._Element) -> AddressBlock:
    usage = text(elem, "usage")
    return AddressBlock(
        name=text(elem, "name") or "",
        range=text(elem, "range") or "",
        width=text(elem, "width") or "",
        base_address=text(elem, "baseAddress"),
        usage=UsageType(usage) if usage else None,
        volatile=bool_text(elem, "volatile"),
        access_policies=_parse_access_policies(elem),
        registers=_parse_registers(elem),
        misalignment_allowed=attr_bool(elem, "misalignmentAllowed", True),
        display_name=text(elem, "displayName"),
        description=text(elem, "description"),
        parameters=parse_parameters(elem),
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
        items=_parse_memory_map_items(elem),
        usage=UsageType(usage) if usage else None,
        volatile=bool_text(elem, "volatile"),
        access_policies=_parse_access_policies(elem),
        parameters=parse_parameters(elem),
        display_name=text(elem, "displayName"),
        description=text(elem, "description"),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_local_memory_map(elem: etree._Element) -> LocalMemoryMap:
    return LocalMemoryMap(
        name=text(elem, "name") or "",
        items=_parse_memory_map_items(elem, allow_subspace=False),
        display_name=text(elem, "displayName"),
        description=text(elem, "description"),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_memory_remap(elem: etree._Element) -> MemoryRemap:
    return MemoryRemap(
        name=text(elem, "name") or "",
        mode_refs=parse_mode_refs(elem),
        items=_parse_memory_map_items(elem),
        display_name=text(elem, "displayName"),
        description=text(elem, "description"),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_memory_map(elem: etree._Element) -> MemoryMap:
    shared = text(elem, "shared")
    return MemoryMap(
        name=text(elem, "name") or "",
        items=_parse_memory_map_items(elem),
        memory_remaps=[_parse_memory_remap(e) for e in children(elem, "memoryRemap")],
        address_unit_bits=text(elem, "addressUnitBits"),
        shared=SharedType(shared) if shared else None,
        display_name=text(elem, "displayName"),
        description=text(elem, "description"),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_segment(elem: etree._Element) -> Segment:
    return Segment(
        name=text(elem, "name") or "",
        address_offset=text(elem, "addressOffset") or "",
        range=text(elem, "range") or "",
        display_name=text(elem, "displayName"),
        description=text(elem, "description"),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_address_space(elem: etree._Element) -> AddressSpace:
    local_memory_map_elem = child(elem, "localMemoryMap")
    return AddressSpace(
        name=text(elem, "name") or "",
        range=text(elem, "range") or "",
        width=text(elem, "width") or "",
        segments=parse_children(elem, "segments", "segment", _parse_segment),
        address_unit_bits=text(elem, "addressUnitBits"),
        local_memory_map=_parse_local_memory_map(local_memory_map_elem) if local_memory_map_elem is not None else None,
        display_name=text(elem, "displayName"),
        description=text(elem, "description"),
        parameters=parse_parameters(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


# --- ports / model ---


def _parse_clock_driver(elem: etree._Element) -> ClockDriver:
    period_elem = child(elem, "clockPeriod")
    offset_elem = child(elem, "clockPulseOffset")
    duration_elem = child(elem, "clockPulseDuration")
    return ClockDriver(
        clock_period=elem_text(period_elem) or "",
        clock_pulse_offset=elem_text(offset_elem) or "",
        clock_pulse_value=text(elem, "clockPulseValue") or "",
        clock_pulse_duration=elem_text(duration_elem) or "",
        clock_name=elem.get("clockName"),
        period_units=period_elem.get("units", "ns") if period_elem is not None else "ns",
        offset_units=offset_elem.get("units", "ns") if offset_elem is not None else "ns",
        duration_units=duration_elem.get("units", "ns") if duration_elem is not None else "ns",
    )


def _parse_single_shot_driver(elem: etree._Element) -> SingleShotDriver:
    offset_elem = child(elem, "singleShotOffset")
    duration_elem = child(elem, "singleShotDuration")
    return SingleShotDriver(
        single_shot_offset=elem_text(offset_elem) or "",
        single_shot_value=text(elem, "singleShotValue") or "",
        single_shot_duration=elem_text(duration_elem) or "",
        offset_units=offset_elem.get("units", "ns") if offset_elem is not None else "ns",
        duration_units=duration_elem.get("units", "ns") if duration_elem is not None else "ns",
    )


def _parse_driver(elem: etree._Element) -> Driver:
    range_elem = child(elem, "range")
    clock_driver_elem = child(elem, "clockDriver")
    single_shot_elem = child(elem, "singleShotDriver")
    return Driver(
        default_value=text(elem, "defaultValue"),
        clock_driver=_parse_clock_driver(clock_driver_elem) if clock_driver_elem is not None else None,
        single_shot_driver=_parse_single_shot_driver(single_shot_elem) if single_shot_elem is not None else None,
        range_left=text(range_elem, "left") if range_elem is not None else None,
        range_right=text(range_elem, "right") if range_elem is not None else None,
        view_refs=texts(elem, "viewRef"),
    )


def _parse_constraint_set(elem: etree._Element) -> ConstraintSet:
    vector_elem = child(elem, "vector")
    return ConstraintSet(
        name=text(elem, "name"),
        vector_left=text(vector_elem, "left") if vector_elem is not None else None,
        vector_right=text(vector_elem, "right") if vector_elem is not None else None,
        drive_constraint=parse_drive_constraint(elem),
        load_constraint=parse_load_constraint(elem),
        timing_constraints=parse_timing_constraints(elem),
        constraint_set_id=elem.get("constraintSetId", "default"),
    )


def _parse_wire_port(elem: etree._Element) -> WirePort:
    direction = elem_text(child(elem, "direction"))
    return WirePort(
        direction=Direction(direction) if direction else Direction.IN,
        qualifier=parse_qualifier(elem),
        vectors=parse_vectors(elem),
        drivers=parse_children(elem, "drivers", "driver", _parse_driver),
        constraint_sets=parse_children(elem, "constraintSets", "constraintSet", _parse_constraint_set),
        all_logical_directions_allowed=attr_bool(elem, "allLogicalDirectionsAllowed", False),
    )


def _parse_transactional_port(elem: etree._Element) -> TransactionalPort:
    initiative = elem_text(child(elem, "initiative"))
    kind_elem = child(elem, "kind")
    connection_elem = child(elem, "connection")
    return TransactionalPort(
        initiative=Initiative(initiative) if initiative else Initiative.REQUIRES,
        kind=elem_text(kind_elem),
        bus_width=text(elem, "busWidth"),
        qualifier=parse_qualifier(elem),
        protocol=parse_protocol(elem),
        max_connections=text(connection_elem, "maxConnections") if connection_elem is not None else None,
        min_connections=text(connection_elem, "minConnections") if connection_elem is not None else None,
        all_logical_initiatives_allowed=attr_bool(elem, "allLogicalInitiativesAllowed", False),
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
        display_name=text(elem, "displayName"),
        description=text(elem, "description"),
        is_io=as_bool(elem.get("isIO")),
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
    )


def _parse_field_map(elem: etree._Element) -> FieldMap:
    return FieldMap(
        field_slice=_parse_field_reference(child(elem, "fieldSlice")),
        sub_port_refs=parse_sub_port_references(elem),
        part_select=parse_part_select(elem),
        mode_refs=parse_mode_refs(elem),
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
        display_name=text(elem, "displayName"),
        description=text(elem, "description"),
        parameters=parse_parameters(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_view(elem: etree._Element) -> View:
    return View(
        name=text(elem, "name") or "",
        env_identifiers=texts(elem, "envIdentifier"),
        component_instantiation_ref=text(elem, "componentInstantiationRef"),
        design_instantiation_ref=text(elem, "designInstantiationRef"),
        design_configuration_instantiation_ref=text(elem, "designConfigurationInstantiationRef"),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_module_parameter(elem: etree._Element) -> ModuleParameter:
    base = parse_parameter(elem)
    constrained = elem.get("constrained")
    return ModuleParameter(
        **vars(base),
        data_type=elem.get("dataType"),
        usage_type=elem.get("usageType", "typed"),
        data_type_definition=elem.get("dataTypeDefinition"),
        constrained=constrained.split() if constrained else [],
    )


def _parse_file_builder_override(elem: etree._Element) -> FileBuilderOverride:
    return FileBuilderOverride(
        file_type=text(elem, "fileType") or "",
        command=text(elem, "command"),
        flags=text(elem, "flags"),
        replace_default_flags=text(elem, "replaceDefaultFlags"),
    )


def _parse_component_instantiation(elem: etree._Element) -> ComponentInstantiation:
    return ComponentInstantiation(
        name=text(elem, "name") or "",
        is_virtual=bool_text(elem, "isVirtual", False),
        language=text(elem, "language"),
        library_name=text(elem, "libraryName"),
        package_name=text(elem, "packageName"),
        module_name=text(elem, "moduleName"),
        architecture_name=text(elem, "architectureName"),
        configuration_name=text(elem, "configurationName"),
        module_parameters=parse_children(elem, "moduleParameters", "moduleParameter", _parse_module_parameter),
        default_file_builders=[_parse_file_builder_override(b) for b in children(elem, "defaultFileBuilder")],
        file_set_refs=_parse_file_set_refs(elem),
        constraint_set_refs=_parse_constraint_set_refs(elem),
        parameters=parse_parameters(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_design_instantiation(elem: etree._Element) -> DesignInstantiation:
    return DesignInstantiation(
        name=text(elem, "name") or "",
        design_ref=parse_vlnv_ref(child(elem, "designRef")),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_design_configuration_instantiation(elem: etree._Element) -> DesignConfigurationInstantiation:
    return DesignConfigurationInstantiation(
        name=text(elem, "name") or "",
        design_configuration_ref=parse_vlnv_ref(child(elem, "designConfigurationRef")),
        language=text(elem, "language"),
        parameters=parse_parameters(elem),
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
        address_offset=text(elem, "addressOffset") or "",
        range=text(elem, "range") or "",
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_cpu(elem: etree._Element) -> Cpu:
    return Cpu(
        name=text(elem, "name") or "",
        range=text(elem, "range") or "",
        width=text(elem, "width") or "",
        memory_map_ref=text(elem, "memoryMapRef") or "",
        regions=parse_children(elem, "regions", "region", _parse_cpu_region),
        address_unit_bits=text(elem, "addressUnitBits"),
        parameters=parse_parameters(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_power_domain(elem: etree._Element) -> PowerDomain:
    return PowerDomain(
        name=text(elem, "name") or "",
        always_on=text(elem, "alwaysOn"),
        sub_domain_of=text(elem, "subDomainOf"),
        parameters=parse_parameters(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_clearbox_element(elem: etree._Element) -> ClearboxElement:
    return ClearboxElement(
        name=text(elem, "name") or "",
        clearbox_type=text(elem, "clearboxType") or "",
        driveable=bool_text(elem, "driveable", False),
        parameters=parse_parameters(elem),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_component_generator(elem: etree._Element) -> ComponentGenerator:
    api_type_elem = child(elem, "apiType")
    return ComponentGenerator(
        name=text(elem, "name") or "",
        generator_exe=text(elem, "generatorExe") or "",
        phase=text(elem, "phase"),
        parameters=parse_parameters(elem),
        api_type=elem_text(api_type_elem),
        api_service=text(elem, "apiService") or "SOAP",
        transport_methods=parse_texts(elem, "transportMethods", "transportMethod"),
        groups=texts(elem, "group"),
        scope=elem.get("scope", "instance"),
        hidden=attr_bool(elem, "hidden", False),
        vendor_extensions=parse_vendor_extensions(elem),
    )


def _parse_reset_type(elem: etree._Element) -> ResetType:
    return ResetType(
        name=text(elem, "name") or "",
        display_name=text(elem, "displayName"),
        description=text(elem, "description"),
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
    )


def _parse_external_type_definitions_ref(elem: etree._Element) -> ExternalTypeDefinitionsRef:
    ref_elem = child(elem, "typeDefinitionsRef")
    return ExternalTypeDefinitionsRef(
        type_definitions=parse_vlnv_ref(ref_elem) if ref_elem is not None else VLNVRef("", "", "", ""),
        name=text(elem, "name"),
    )
