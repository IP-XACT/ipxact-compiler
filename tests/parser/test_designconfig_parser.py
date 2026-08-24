"""Parses a real IP-XACT design configuration XML fixture (configuring the top_design.xml
fixture) and checks the resulting object model matches the source file, exercising the
designconfig_parser end to end.
"""

from pathlib import Path

from ipxact.parser.main_parser import parse_file

FIXTURE = Path(__file__).parent / "xml" / "top_design_config.xml"


def test_design_configuration_vlnv_and_design_ref():
    design_config = parse_file(FIXTURE)
    assert str(design_config.vlnv) == "example.org:soc:top_design_config:1.0"
    assert str(design_config.design_ref) == "example.org:soc:top_design:1.0"


def test_interconnection_configuration_abstractor_chain():
    design_config = parse_file(FIXTURE)
    interconnection_configuration = design_config.interconnection_configurations[0]
    assert interconnection_configuration.interconnection_ref == "cpu_apb_conn"

    chain = interconnection_configuration.abstractor_chains[0]
    assert chain.interface_refs[0].component_ref == "cpu"
    assert chain.interface_refs[0].bus_ref == "apb"

    abstractor = chain.abstractors[0]
    assert abstractor.instance_name == "apb_bridge0"
    assert str(abstractor.abstractor_ref) == "example.org:abstractors:apb_bridge:1.0"
    assert abstractor.view_name == "rtl"


def test_view_configurations():
    design_config = parse_file(FIXTURE)
    by_instance = {vc.instance_name: vc for vc in design_config.view_configurations}

    cpu_view = by_instance["cpu"]
    assert cpu_view.view_ref == "rtl"
    assert cpu_view.configurable_element_values == {"ICACHE_ECC": "1"}

    uart_view = by_instance["uart0"]
    assert uart_view.view_ref == "rtl"
    assert uart_view.configurable_element_values == {}
