"""Parses full_component.xml, a component using the parts of componentType that apb_uart.xml
does not, and checks each of them reaches the object model.
"""

from pathlib import Path

import pytest

from ipxact.parser.main_parser import parse_file
from ipxact.schema.businterface import InterfaceMode
from ipxact.schema.common import DefinitionRef, Expression, IndexedRef, TextValue
from ipxact.schema.memorymap import ReadAction

FIXTURE = Path(__file__).parent / "xml" / "full_component.xml"
ACME = "{http://acme.example/ipxact}"


@pytest.fixture(scope="module")
def component():
    return parse_file(FIXTURE)


def _block(component):
    return component.memory_maps[0].items[0]


def _register(component, name):
    return next(r for r in _block(component).registers if r.name == name)


def _port(component, name):
    return next(p for p in component.model.ports if p.name == name)


# --- expressions, xml:id, attributes from other namespaces ---


def test_expression_keeps_bounds_and_other_attributes(component):
    apb = component.bus_interfaces[0]
    assert apb.bits_in_lau == Expression(
        value="8", minimum="8", maximum="32", other_attributes={f"{ACME}unit": "bits"}
    )


def test_xml_id_and_other_attributes_on_elements(component):
    apb = component.bus_interfaces[0]
    assert component.xml_id == "comp"
    assert apb.xml_id == "bi_apb"
    assert apb.other_attributes == {f"{ACME}priority": "high"}
    assert apb.abstraction_types[0].view_refs == [TextValue("rtl", xml_id="vr_abs")]
    assert component.model.views[0].env_identifiers == [TextValue(":modelsim.mentor.com:", xml_id="env_sv")]


def test_mirrored_initiator_keeps_other_attributes_and_text(component):
    mon = component.bus_interfaces[1]
    assert mon.mode is InterfaceMode.MIRRORED_INITIATOR
    assert mon.mirrored_initiator.other_attributes == {f"{ACME}role": "snoop"}
    assert mon.mirrored_initiator.text == "snoop only"


def test_name_group_fields(component):
    view = component.model.views[0]
    assert (view.display_name, view.description) == ("RTL view", "Synthesizable RTL")
    assert component.bus_interfaces[0].short_description == "APB target"
    assert _register(component, "DATA").short_description == "channel data"
    assert component.file_sets[0].files[0].description == "standard cells"


def test_vendor_extensions_have_no_trailing_whitespace(component):
    assert len(component.vendor_extensions) == 1
    assert component.vendor_extensions[0].endswith(">team-a</acme:owner>")


# --- memory maps, registers and field references ---


def test_address_block_array_and_type_identifier(component):
    block = _block(component)
    assert block.array.dims[0].size.value == "4"
    assert block.array.dims[0].index_var == "i"
    assert block.array.stride.value == "0x100"
    assert block.type_identifier == "chan_t"


def test_sliced_and_simple_access_handles(component):
    block_handle = _block(component).access_handles[0]
    assert block_handle.force is False
    assert block_handle.view_refs == [TextValue("rtl")]
    assert block_handle.slices_xml_id == "sl_chan"
    assert [s.value for s in block_handle.slices[0].path_segments] == ["u_chan"]

    register_handle = _register(component, "DATA").access_handles[0]
    assert register_handle.force is True
    assert [s.value for s in register_handle.path_segments] == ["u_regs", "data_q"]


def test_field_access_policy_modify_and_broadcast(component):
    val = _register(component, "DATA").fields[0]
    assert val.field_access_policies_xml_id == "fap_val"
    policy = val.field_access_policies[0]
    assert policy.read_action is ReadAction.MODIFY
    assert policy.read_action_modify == "pop_fifo"
    broadcast = policy.broadcast_to[0]
    assert broadcast.xml_id == "bc_shadow"
    assert broadcast.address_block_ref == IndexedRef("chan")
    assert broadcast.register_ref == IndexedRef("SHADOW")
    assert broadcast.field_ref == IndexedRef("VAL")


def test_definition_refs_and_alias(component):
    val, val_hi = _register(component, "DATA").fields
    assert val.enumeration_definition_ref == DefinitionRef("val_enum", type_definitions="regdefs")
    assert val.enumerated_values == []

    assert val_hi.bit_width is None
    assert val_hi.alias_of.register_ref == IndexedRef("SHADOW")
    assert val_hi.alias_of.field_ref == IndexedRef("VAL")

    shadow = _register(component, "SHADOW")
    assert shadow.register_definition_ref == DefinitionRef("shadow_reg", type_definitions="regdefs")
    assert shadow.size is None


def test_field_slice_reference_keeps_indices(component):
    field_slice = component.modes[0].field_slices[0]
    assert field_slice.xml_id == "fs_chan3"
    field_ref = field_slice.field_ref
    assert field_ref.xml_id is None
    assert field_ref.memory_map_ref == "mm"
    assert field_ref.address_block_ref.name == "chan"
    assert [i.value for i in field_ref.address_block_ref.indices] == ["3"]


# --- ports, bus interfaces and model ---


def test_port_map_logical_range(component):
    port_map = component.bus_interfaces[0].abstraction_types[0].port_maps[0]
    assert port_map.logical_port == "PADDR"
    assert port_map.logical_port_xml_id == "lp_paddr"
    assert port_map.logical_range.left.value == "11"
    assert port_map.logical_range.right.value == "0"


def test_wire_type_defs_and_power_constraints(component):
    wire = _port(component, "paddr").wire
    type_def = wire.wire_type_defs[0]
    assert type_def.type_name == "std_logic_vector"
    assert type_def.type_name_constrained == ["length"]
    assert type_def.type_definitions == [TextValue("IEEE.std_logic_1164.all")]
    assert wire.signal_type_defs[0].signal_type == "digital"
    constraint = wire.power_constraints[0]
    assert constraint.power_domain_ref == "pd_core"
    assert constraint.range.left.value == "7"
    assert wire.constraint_sets[0].drive_constraint.cell.cell_function_other == "nor3"


def test_port_access(component):
    access = _port(component, "paddr").access
    assert access.port_access_type == "ref"
    assert [s.value for s in access.access_handles[0].slices[0].path_segments] == ["paddr_i"]


def test_transactional_kind_custom_and_type_defs(component):
    transactional = _port(component, "sock").transactional
    assert transactional.kind == "custom"
    assert transactional.kind_custom == "my_socket"
    trans_type_def = transactional.trans_type_defs[0]
    assert trans_type_def.type_name == "tlm_target_socket"
    assert trans_type_def.type_name_exact is False
    service = trans_type_def.service_type_defs[0]
    assert service.type_name == "tlm_fw_transport_if"
    assert service.type_name_implicit is True


def test_component_instantiation_language_and_clearbox_refs(component):
    instantiation = component.model.component_instantiations[0]
    assert instantiation.language == "systemverilog"
    assert instantiation.language_strict is True
    assert instantiation.file_set_refs[0].local_name == "rtl_files"
    assert instantiation.file_set_refs[0].xml_id == "fsr_rtl"
    clearbox_ref = instantiation.clearbox_element_refs[0]
    assert clearbox_ref.name == "cb_state"
    assert [s.value for s in clearbox_ref.locations[0].slices[0].path_segments] == ["u_fsm", "state_q"]


# --- files, file sets, CPUs and type definitions ---


def test_file_details(component):
    file = component.file_sets[0].files[0]
    assert file.file_id == "f_lib"
    assert file.other_attributes == {f"{ACME}origin": "vendor"}
    assert file.file_types[0].value == "user"
    assert file.file_types[0].user == "libertyLibrary"
    assert file.file_types[0].libext == "lib"
    assert file.logical_name == "cells"
    assert file.logical_name_default is True
    assert file.build_command.command.value == "lc_shell"
    assert file.build_command.flags.value == "-f"
    assert file.build_command.flags_append is True
    assert file.build_command.target_name == "cells.db"
    assert file.defines[0].name == "SIM"
    assert file.defines[0].value.value == "1"
    assert file.image_types == [TextValue("liberty")]


def test_file_set_function(component):
    function = component.file_sets[0].functions[0]
    assert function.replicate is True
    assert function.entry_point == "init_chan"
    assert function.file_ref == "f_lib"
    assert function.return_type == "int"
    assert function.arguments[0].data_type == "unsigned int"
    assert function.arguments[0].value.value == "3"
    assert function.source_files[0].source_name == "sw/init.c"
    assert function.source_files[0].file_type.value == "cSource"


def test_cpu_executable_image(component):
    image = component.cpus[0].executable_images[0]
    assert image.name == "bootloader"
    assert image.image_id == "boot"
    assert image.image_type == "elf"
    tools = image.language_tools
    assert tools.file_builders[0].command.value == "gcc"
    assert tools.linker.value == "ld"
    assert tools.linker_flags.value == "-nostdlib"
    assert tools.linker_command_file.name.value == "boot.ld"
    assert image.file_set_ref_group.file_set_refs[0].local_name == "rtl_files"


def test_type_definitions_links(component):
    type_defs = component.external_type_definitions[0]
    assert type_defs.name == "regdefs"
    assert (type_defs.view_links[0].external_view_ref, type_defs.view_links[0].view_ref) == ("ext_rtl", "rtl")
    assert (type_defs.mode_links[0].external_mode_ref, type_defs.mode_links[0].mode_ref) == ("ext_normal", "normal")
    assert (type_defs.reset_type_links[0].external_reset_type_ref, type_defs.reset_type_links[0].reset_type_ref) == (
        "ext_soft",
        "soft",
    )
