"""Builds a small APB UART component by hand to sanity-check that the object model can
represent a real IP-XACT component end to end.
"""

from ipxact import (
    AccessType,
    AddressBlock,
    BusInterface,
    Component,
    Direction,
    InterfaceMode,
    MemoryMap,
    Model,
    Parameter,
    Port,
    PortMap,
    VLNV,
    VLNVRef,
    Vector,
    WirePort,
)
from ipxact.schema.businterface import AbstractionType


def build_apb_uart() -> Component:
    apb = BusInterface(
        name="apb",
        bus_type=VLNVRef("amba.com", "AMBA4", "APB4", "r0p0_0"),
        mode=InterfaceMode.TARGET,
        abstraction_types=[
            AbstractionType(
                abstraction_ref=VLNVRef("amba.com", "AMBA4", "APB4_rtl", "r0p0_0"),
                port_maps=[PortMap(logical_port="PCLK", physical_port="clk")],
            )
        ],
    )

    memory_map = MemoryMap(
        name="apb_uart_mm",
        items=[AddressBlock(name="regs", base_address="0x0", range="0x100", width="32")],
    )

    model = Model(
        ports=[
            Port(name="clk", wire=WirePort(direction=Direction.IN)),
            Port(name="rst_n", wire=WirePort(direction=Direction.IN)),
        ]
    )

    return Component(
        vlnv=VLNV("example.org", "ip", "apb_uart", "1.0"),
        bus_interfaces=[apb],
        memory_maps=[memory_map],
        model=model,
        parameters=[Parameter(name="BAUD_RATE", value="115200", parameter_id="BAUD_RATE")],
    )


def test_apb_uart_vlnv():
    component = build_apb_uart()
    assert str(component.vlnv) == "example.org:ip:apb_uart:1.0"


def test_apb_uart_bus_interface_resolves_to_apb4():
    component = build_apb_uart()
    apb = component.bus_interfaces[0]
    assert apb.mode is InterfaceMode.TARGET
    assert str(apb.bus_type) == "amba.com:AMBA4:APB4:r0p0_0"
    assert apb.abstraction_types[0].port_maps[0].physical_port == "clk"


def test_apb_uart_memory_map():
    component = build_apb_uart()
    block = component.memory_maps[0].items[0]
    assert isinstance(block, AddressBlock)
    assert block.base_address == "0x0"
    assert block.range == "0x100"


def test_apb_uart_ports():
    component = build_apb_uart()
    assert [p.name for p in component.model.ports] == ["clk", "rst_n"]
    assert component.model.ports[0].wire.direction is Direction.IN


def test_wire_port_vectors_are_expressions():
    port = Port(
        name="data",
        wire=WirePort(direction=Direction.OUT, vectors=[Vector(left="7", right="0")]),
    )
    assert port.wire.vectors[0].left == "7"


def test_address_block_defaults():
    block = AddressBlock(name="regs", base_address="0x0", range="0x4", width="32")
    assert block.registers == []
    assert AccessType.READ_WRITE.value == "read-write"
