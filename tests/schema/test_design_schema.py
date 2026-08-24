"""Builds a small top-level design by hand to sanity-check that the object model can
represent a real IP-XACT design end to end.
"""

from ipxact import (
    ActiveInterface,
    AdHocConnection,
    ComponentInstance,
    Design,
    Interconnection,
    InternalPortReference,
    VLNV,
    VLNVRef,
)


def build_top_design() -> Design:
    uart0 = ComponentInstance(
        instance_name="uart0",
        component_ref=VLNVRef("example.org", "ip", "apb_uart", "1.0"),
    )
    apb_bus = ComponentInstance(
        instance_name="apb_bus",
        component_ref=VLNVRef("example.org", "ip", "apb_interconnect", "2.0"),
    )

    interconnection = Interconnection(
        name="apb_uart0_conn",
        active_interface=ActiveInterface(component_instance_ref="apb_bus", bus_ref="apb_m0"),
        other_active_interfaces=[
            ActiveInterface(component_instance_ref="uart0", bus_ref="apb"),
        ],
    )

    clk_net = AdHocConnection(
        name="clk_net",
        internal_port_references=[
            InternalPortReference(component_instance_ref="uart0", port_ref="clk"),
            InternalPortReference(component_instance_ref="apb_bus", port_ref="clk"),
        ],
    )

    return Design(
        vlnv=VLNV("example.org", "soc", "top_design", "1.0"),
        component_instances=[uart0, apb_bus],
        interconnections=[interconnection],
        ad_hoc_connections=[clk_net],
    )


def test_top_design_vlnv():
    design = build_top_design()
    assert str(design.vlnv) == "example.org:soc:top_design:1.0"


def test_top_design_component_instances():
    design = build_top_design()
    names = [instance.instance_name for instance in design.component_instances]
    assert names == ["uart0", "apb_bus"]
    assert str(design.component_instances[0].component_ref) == "example.org:ip:apb_uart:1.0"


def test_top_design_interconnection_endpoints():
    design = build_top_design()
    conn = design.interconnections[0]
    assert conn.active_interface.component_instance_ref == "apb_bus"
    assert conn.active_interface.bus_ref == "apb_m0"
    assert conn.other_active_interfaces[0].component_instance_ref == "uart0"


def test_top_design_ad_hoc_connection():
    design = build_top_design()
    conn = design.ad_hoc_connections[0]
    refs = {(r.component_instance_ref, r.port_ref) for r in conn.internal_port_references}
    assert refs == {("uart0", "clk"), ("apb_bus", "clk")}
