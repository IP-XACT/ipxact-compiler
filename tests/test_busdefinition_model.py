"""Builds a small APB4-style bus definition and abstraction definition by hand to sanity-check
that the object model can represent real IP-XACT bus/abstraction documents end to end.
"""

from ipxact import (
    AbstractionDefinition,
    AbstractionPort,
    BusDefinition,
    Direction,
    Presence,
    Qualifier,
    VLNV,
    VLNVRef,
    WireAbstractionPort,
    WireModeConstraints,
)


def build_apb4_bus_definition() -> BusDefinition:
    return BusDefinition(
        vlnv=VLNV("amba.com", "AMBA4", "APB4", "r0p0_0"),
        direct_connection=True,
        is_addressable=True,
        max_initiators="1",
    )


def build_apb4_abstraction_definition() -> AbstractionDefinition:
    pclk = AbstractionPort(
        logical_name="PCLK",
        wire=WireAbstractionPort(
            qualifier=Qualifier(is_clock=True),
            on_initiator=WireModeConstraints(presence=Presence.REQUIRED, direction=Direction.OUT.value),
            on_target=WireModeConstraints(presence=Presence.REQUIRED, direction=Direction.IN.value),
        ),
    )
    pwdata = AbstractionPort(
        logical_name="PWDATA",
        wire=WireAbstractionPort(
            qualifier=Qualifier(is_data=True),
            on_initiator=WireModeConstraints(presence=Presence.OPTIONAL, direction=Direction.OUT.value),
            on_target=WireModeConstraints(presence=Presence.OPTIONAL, direction=Direction.IN.value),
        ),
    )

    return AbstractionDefinition(
        vlnv=VLNV("amba.com", "AMBA4", "APB4_rtl", "r0p0_0"),
        bus_type=VLNVRef("amba.com", "AMBA4", "APB4", "r0p0_0"),
        ports=[pclk, pwdata],
    )


def test_bus_definition_vlnv_and_topology():
    bus_def = build_apb4_bus_definition()
    assert str(bus_def.vlnv) == "amba.com:AMBA4:APB4:r0p0_0"
    assert bus_def.direct_connection is True
    assert bus_def.is_addressable is True
    assert bus_def.max_initiators == "1"
    assert bus_def.max_targets is None


def test_abstraction_definition_references_bus_definition():
    abs_def = build_apb4_abstraction_definition()
    assert str(abs_def.bus_type) == "amba.com:AMBA4:APB4:r0p0_0"
    assert [p.logical_name for p in abs_def.ports] == ["PCLK", "PWDATA"]


def test_abstraction_definition_port_presence_and_direction():
    abs_def = build_apb4_abstraction_definition()
    pclk = abs_def.ports[0]
    assert pclk.wire.qualifier.is_clock is True
    assert pclk.wire.on_initiator.presence is Presence.REQUIRED
    assert pclk.wire.on_initiator.direction == "out"
    assert pclk.wire.on_target.direction == "in"


def test_abstraction_definition_optional_data_port():
    abs_def = build_apb4_abstraction_definition()
    pwdata = abs_def.ports[1]
    assert pwdata.wire.qualifier.is_data is True
    assert pwdata.wire.on_initiator.presence is Presence.OPTIONAL
