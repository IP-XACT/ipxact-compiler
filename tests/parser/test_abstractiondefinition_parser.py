"""Parses a real IP-XACT abstraction definition XML fixture (APB4 at RTL level) and checks
the resulting object model matches the source file, exercising the
abstractiondefinition_parser end to end.
"""

from pathlib import Path

from lxml import etree

from ipxact.parser.abstractiondefinition_parser import _parse_wire_mode_constraints
from ipxact.parser.main_parser import parse_file
from ipxact.schema.abstractiondefinition import Presence

FIXTURE = Path(__file__).parent / "xml" / "apb4_abstractiondefinition.xml"


def test_abstraction_definition_vlnv_and_bus_type():
    abs_def = parse_file(FIXTURE)
    assert str(abs_def.vlnv) == "amba.com:AMBA4:APB4_rtl:r0p0_0"
    assert str(abs_def.bus_type) == "amba.com:AMBA4:APB4:r0p0_0"


def test_clock_port_is_required_both_directions():
    abs_def = parse_file(FIXTURE)
    pclk = next(p for p in abs_def.ports if p.logical_name == "PCLK")
    assert pclk.wire.qualifier.is_clock is True
    assert pclk.wire.on_initiator.presence is Presence.REQUIRED
    assert pclk.wire.on_initiator.direction == "out"
    assert pclk.wire.on_target.presence is Presence.REQUIRED
    assert pclk.wire.on_target.direction == "in"


def test_data_port_is_optional_with_width():
    abs_def = parse_file(FIXTURE)
    pwdata = next(p for p in abs_def.ports if p.logical_name == "PWDATA")
    assert pwdata.wire.qualifier.is_data is True
    assert pwdata.wire.on_initiator.presence is Presence.OPTIONAL
    assert pwdata.wire.on_initiator.width == "32"
    assert pwdata.wire.on_initiator.width_all_bits_required is True


def test_pretty_printed_presence_does_not_crash():
    """Regression test: a pretty-printed <presence> with indentation whitespace around its
    text used to raise ValueError from Presence(raw_text) instead of matching the enum.
    """
    ns = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"
    elem = etree.fromstring(
        f'<ipxact:onInitiator xmlns:ipxact="{ns}">\n'
        "  <ipxact:presence>\n    required\n  </ipxact:presence>\n"
        "</ipxact:onInitiator>"
    )
    assert _parse_wire_mode_constraints(elem).presence is Presence.REQUIRED
