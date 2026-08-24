"""Parses a real (minimal) IP-XACT component XML fixture and checks the resulting object
model matches the source file, exercising the component_parser end to end.
"""

from pathlib import Path

from ipxact.parser.main_parser import parse_file
from ipxact.schema.businterface import InterfaceMode
from ipxact.schema.memorymap import AddressBlock
from ipxact.schema.ports import Direction

FIXTURE = Path(__file__).parent / "fixtures" / "apb_uart.xml"


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
