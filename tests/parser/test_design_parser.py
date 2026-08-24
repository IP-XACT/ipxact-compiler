"""Parses a real IP-XACT design XML fixture (a small SoC: a core, a UART, a timer, a debug
module, and an APB interconnect) and checks the resulting object model matches the source
file, exercising the design_parser end to end.
"""

from pathlib import Path

from ipxact.parser.main_parser import parse_file

FIXTURE = Path(__file__).parent / "xml" / "top_design.xml"


def test_design_vlnv():
    design = parse_file(FIXTURE)
    assert str(design.vlnv) == "example.org:soc:top_design:1.0"


def test_component_instances():
    design = parse_file(FIXTURE)
    names = [instance.instance_name for instance in design.component_instances]
    assert names == ["cpu", "uart0", "timer0", "debug0", "apb_bus"]
    refs = {instance.instance_name: str(instance.component_ref) for instance in design.component_instances}
    assert refs["cpu"] == "example.org:ip:riscv_core:1.0"
    assert refs["uart0"] == "example.org:ip:apb_uart:1.0"
    assert refs["timer0"] == "example.org:ip:apb_timer:1.0"
    assert refs["debug0"] == "example.org:ip:debug_module:1.0"
    assert refs["apb_bus"] == "example.org:ip:apb_interconnect:2.0"


def test_bus_interconnections():
    design = parse_file(FIXTURE)
    assert [c.name for c in design.interconnections] == [
        "cpu_apb_conn",
        "bus_uart0_conn",
        "bus_timer0_conn",
    ]

    cpu_conn = design.interconnections[0]
    assert cpu_conn.active_interface.component_instance_ref == "cpu"
    assert cpu_conn.active_interface.bus_ref == "apb"
    assert cpu_conn.other_active_interfaces[0].component_instance_ref == "apb_bus"
    assert cpu_conn.other_active_interfaces[0].bus_ref == "apb_t"
    assert cpu_conn.short_description == "CPU to bus link"

    uart_conn = design.interconnections[1]
    assert uart_conn.active_interface.component_instance_ref == "apb_bus"
    assert uart_conn.active_interface.bus_ref == "apb_m0"
    assert uart_conn.other_active_interfaces[0].component_instance_ref == "uart0"


def test_clock_ad_hoc_connection_fans_out_to_every_instance():
    design = parse_file(FIXTURE)
    clk_net = next(c for c in design.ad_hoc_connections if c.name == "clk_net")
    refs = {r.component_instance_ref for r in clk_net.internal_port_references}
    assert refs == {"cpu", "uart0", "timer0", "debug0", "apb_bus"}
    assert all(r.port_ref == "clk" for r in clk_net.internal_port_references)
    assert clk_net.short_description == "Shared system clock"


def test_debug_signal_ad_hoc_connections():
    design = parse_file(FIXTURE)
    req_net = next(c for c in design.ad_hoc_connections if c.name == "debug_req_net")
    refs = {(r.component_instance_ref, r.port_ref) for r in req_net.internal_port_references}
    assert refs == {("debug0", "debug_req_o"), ("cpu", "debug_req_i")}

    resp_net = next(c for c in design.ad_hoc_connections if c.name == "debug_resp_net")
    refs = {(r.component_instance_ref, r.port_ref) for r in resp_net.internal_port_references}
    assert refs == {("cpu", "debug_resp_o"), ("debug0", "debug_resp_i")}
