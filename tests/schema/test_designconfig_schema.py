"""Builds a small design configuration by hand to sanity-check that the object model can
represent a real IP-XACT design configuration end to end.
"""

from ipxact import (
    AbstractorChain,
    AbstractorInstance,
    DesignConfiguration,
    InterconnectionConfiguration,
    InterfaceRef,
    VLNV,
    VLNVRef,
    ViewConfiguration,
)


def build_design_configuration() -> DesignConfiguration:
    abstractor_chain = AbstractorChain(
        interface_refs=[InterfaceRef(component_ref="uart0", bus_ref="apb")],
        abstractors=[
            AbstractorInstance(
                instance_name="apb_to_axi0",
                abstractor_ref=VLNVRef("example.org", "abstractors", "apb_to_axi", "1.0"),
                view_name="rtl",
            )
        ],
    )

    interconnection_configuration = InterconnectionConfiguration(
        interconnection_ref="apb_uart0_conn",
        abstractor_chains=[abstractor_chain],
    )

    view_configuration = ViewConfiguration(
        instance_name="uart0",
        view_ref="rtl",
        configurable_element_values={"BAUD_RATE": "115200"},
    )

    return DesignConfiguration(
        vlnv=VLNV("example.org", "soc", "top_design", "1.0"),
        design_ref=VLNVRef("example.org", "soc", "top_design", "1.0"),
        interconnection_configurations=[interconnection_configuration],
        view_configurations=[view_configuration],
    )


def test_design_configuration_vlnv_and_design_ref():
    design_config = build_design_configuration()
    assert str(design_config.vlnv) == "example.org:soc:top_design:1.0"
    assert str(design_config.design_ref) == "example.org:soc:top_design:1.0"


def test_design_configuration_abstractor_chain():
    design_config = build_design_configuration()
    interconnection_configuration = design_config.interconnection_configurations[0]
    assert interconnection_configuration.interconnection_ref == "apb_uart0_conn"

    chain = interconnection_configuration.abstractor_chains[0]
    assert chain.interface_refs[0].component_ref == "uart0"
    assert chain.abstractors[0].instance_name == "apb_to_axi0"
    assert str(chain.abstractors[0].abstractor_ref) == "example.org:abstractors:apb_to_axi:1.0"


def test_design_configuration_view_configuration():
    design_config = build_design_configuration()
    view_configuration = design_config.view_configurations[0]
    assert view_configuration.instance_name == "uart0"
    assert view_configuration.view_ref == "rtl"
    assert view_configuration.configurable_element_values["BAUD_RATE"] == "115200"
