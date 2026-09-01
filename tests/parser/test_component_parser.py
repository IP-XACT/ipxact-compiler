"""Parses a real (minimal) IP-XACT component XML fixture and checks the resulting object
model matches the source file, exercising the component_parser end to end.
"""

from pathlib import Path

from lxml import etree

from ipxact.parser.component_parser import _parse_field_access_policy
from ipxact.parser.main_parser import parse_file
from ipxact.schema.businterface import InterfaceMode
from ipxact.schema.memorymap import AddressBlock
from ipxact.schema.memorymap import TestConstraint as FieldTestConstraint
from ipxact.schema.ports import Direction

NS = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"

FIXTURE = Path(__file__).parent / "xml" / "apb_uart.xml"
COMMENT_FIXTURE = Path(__file__).parent / "xml" / "apb_uart_with_comment.xml"


def test_component_vlnv():
    component = parse_file(FIXTURE)
    assert str(component.vlnv) == "example.org:ip:apb_uart:1.0"


def test_bus_interface_target_mode():
    component = parse_file(FIXTURE)
    apb = component.bus_interfaces[0]
    assert apb.name == "apb"
    assert apb.mode is InterfaceMode.TARGET
    assert str(apb.bus_type) == "amba.com:AMBA4:APB4:r0p0_0"
    assert apb.target.memory_map_ref == "apb_uart_mm"
    assert len(apb.target.mode_refs) == 1
    assert apb.target.mode_refs[0].name == "default"
    assert apb.target.mode_refs[0].priority == 1


def test_bus_interface_bit_steering_defaults_to_zero():
    """Regression test: busInterface.xsd declares <bitSteering> with default="0" when
    absent, but the parser used to leave it None instead of applying the schema default.
    """
    component = parse_file(FIXTURE)
    apb = component.bus_interfaces[0]
    assert apb.bit_steering == "0"


def test_field_access_policy_test_constraint_defaults_to_unconstrained():
    """Regression test: memoryMap.xsd's <testable> element declares its testConstraint
    attribute with default="unconstrained" when absent, but the parser used to leave
    test_constraint None instead of applying the schema default.
    """
    elem = etree.fromstring(
        f'<ipxact:fieldAccessPolicy xmlns:ipxact="{NS}"><ipxact:testable>true</ipxact:testable></ipxact:fieldAccessPolicy>'
    )
    policy = _parse_field_access_policy(elem)
    assert policy.testable is True
    assert policy.test_constraint is FieldTestConstraint.UNCONSTRAINED


def test_bus_interface_abstraction_port_map():
    component = parse_file(FIXTURE)
    port_map = component.bus_interfaces[0].abstraction_types[0].port_maps[0]
    assert port_map.logical_port == "PCLK"
    assert port_map.physical_port == "clk"


def test_memory_map_address_block_and_register():
    component = parse_file(FIXTURE)
    block = component.memory_maps[0].items[0]
    assert isinstance(block, AddressBlock)
    assert block.base_address == "0x0"
    assert block.range == "0x100"
    assert block.width == "32"

    register = block.registers[0]
    assert register.name == "CTRL"
    assert register.address_offset == "0x0"
    assert register.size == "32"

    field = register.fields[0]
    assert field.name == "ENABLE"
    assert field.bit_offset == "0"
    assert field.bit_width == "1"


def test_model_ports():
    component = parse_file(FIXTURE)
    assert [p.name for p in component.model.ports] == ["clk", "rst_n"]
    assert component.model.ports[0].wire.direction is Direction.IN


def test_parameters():
    component = parse_file(FIXTURE)
    baud_rate = component.parameters[0]
    assert baud_rate.name == "BAUD_RATE"
    assert baud_rate.value == "115200"
    assert baud_rate.parameter_id == "BAUD_RATE"


def test_comments_do_not_disturb_vlnv_and_description():
    """Comments appear inside vendor/version (before and after the value text) and as the
    sole content of description (no real value at all). A comment placed before an
    element's value text used to make lxml's .text capture only the comment, silently
    pushing the real value onto the comment's .tail and losing it; parse_file must strip
    comments during parsing so this never surfaces downstream.
    """
    component = parse_file(COMMENT_FIXTURE)
    assert str(component.vlnv) == "example.org:ip:apb_uart:1.0"
    assert component.description is None


def test_comments_do_not_disturb_bus_interface_or_port_map():
    """Covers a comment before an attribute-only element, and two comments in a row
    before a value (proving comment removal isn't a one-comment-only fix).
    """
    component = parse_file(COMMENT_FIXTURE)
    apb = component.bus_interfaces[0]
    assert apb.name == "apb"
    assert str(apb.bus_type) == "amba.com:AMBA4:APB4:r0p0_0"
    port_map = apb.abstraction_types[0].port_maps[0]
    assert port_map.logical_port == "PCLK"
    assert port_map.physical_port == "clk"


def test_comments_do_not_disturb_memory_map():
    """Covers comments nested three levels deep (addressBlock -> register -> field)."""
    component = parse_file(COMMENT_FIXTURE)
    block = component.memory_maps[0].items[0]
    assert block.base_address == "0x0"
    field = block.registers[0].fields[0]
    assert field.bit_width == "1"


def test_comments_do_not_disturb_ports_or_parameters():
    """Covers comments between sibling elements (between the three <port> entries) and a
    comment before a value inside a parameter.
    """
    component = parse_file(COMMENT_FIXTURE)
    ports_by_name = {p.name: p.wire.direction for p in component.model.ports}
    assert ports_by_name == {"clk": Direction.IN, "rst_n": Direction.IN, "wdata": Direction.OUT}
    assert component.parameters[0].value == "115200"
