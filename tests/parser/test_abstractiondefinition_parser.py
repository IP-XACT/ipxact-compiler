"""Parses a real IP-XACT abstraction definition XML fixture (APB4 at RTL level) and checks
the resulting object model matches the source file, exercising the
abstractiondefinition_parser end to end.
"""

from pathlib import Path

from lxml import etree

from ipxact.parser.abstractiondefinition_parser import (
    _parse_transactional_mode_constraints,
    _parse_wire_mode_constraints,
)
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
    assert pwdata.wire.on_initiator.width.value == "32"
    assert pwdata.wire.on_initiator.width_all_bits_required is True


def test_wire_mode_direction_absent_empty_or_set():
    """A missing <direction> means the direction is not restricted, so it stays None. The XSD
    default="out" only applies to an element that is present but empty.
    """
    ns = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"
    cases = {
        "": None,
        "<ipxact:direction/>": "out",
        "<ipxact:direction>in</ipxact:direction>": "in",
    }
    for direction_xml, expected in cases.items():
        elem = etree.fromstring(
            f'<ipxact:onInitiator xmlns:ipxact="{ns}">'
            f"<ipxact:presence>required</ipxact:presence>{direction_xml}"
            "</ipxact:onInitiator>"
        )
        assert _parse_wire_mode_constraints(elem).direction == expected


def test_transactional_initiative_absent_empty_or_set():
    """A missing <initiative> means the access type is not restricted, so it stays None. The
    XSD default="requires" only applies to an element that is present but empty.
    """
    ns = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"
    cases = {
        "": None,
        "<ipxact:initiative/>": "requires",
        "<ipxact:initiative>provides</ipxact:initiative>": "provides",
    }
    for initiative_xml, expected in cases.items():
        elem = etree.fromstring(
            f'<ipxact:onInitiator xmlns:ipxact="{ns}">'
            f"<ipxact:presence>required</ipxact:presence>{initiative_xml}"
            "</ipxact:onInitiator>"
        )
        assert _parse_transactional_mode_constraints(elem).initiative == expected


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


PACKET_FIXTURE = Path(__file__).parent / "xml" / "packet_abstractiondefinition.xml"


def test_packets():
    abs_def = parse_file(PACKET_FIXTURE)
    data = next(p for p in abs_def.ports if p.logical_name == "DATA")
    assert data.xml_id == "p_data"
    packet = data.packets[0]
    assert packet.name == "frame"
    assert packet.endianness == "little"
    header, payload = packet.packet_fields
    assert header.width.value == "8"
    assert header.value.value == "'hA5"
    assert header.qualifier.is_opcode is True
    assert payload.width.value == "24"
    assert payload.value is None


def test_transactional_kind_custom_and_on_system_xml_id():
    abs_def = parse_file(PACKET_FIXTURE)
    transactional = next(p for p in abs_def.ports if p.logical_name == "DATA").transactional
    assert transactional.on_initiator.kind_custom == "my_socket"
    assert transactional.on_initiator.bus_width.minimum == "8"
    assert transactional.on_initiator.bus_width.maximum == "64"
    on_system = transactional.on_system[0]
    assert on_system.xml_id == "sys_dbg"
    assert on_system.constraints.kind_custom == "dbg_socket"


def test_cell_function_other():
    abs_def = parse_file(PACKET_FIXTURE)
    clk = next(p for p in abs_def.ports if p.logical_name == "CLK")
    cell = clk.wire.on_target.mode_constraints.drive_constraint.cell
    assert cell.cell_function == "other"
    assert cell.cell_function_other == "clkbuf"
