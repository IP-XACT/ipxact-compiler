"""Parses a real IP-XACT bus definition XML fixture (APB4) and checks the resulting object
model matches the source file, exercising the busdefinition_parser end to end.
"""

from pathlib import Path

from ipxact.parser.main_parser import parse_file

FIXTURE = Path(__file__).parent / "xml" / "apb4_busdefinition.xml"


def test_bus_definition_vlnv():
    bus_def = parse_file(FIXTURE)
    assert str(bus_def.vlnv) == "amba.com:AMBA4:APB4:r0p0_0"


def test_bus_definition_topology():
    bus_def = parse_file(FIXTURE)
    assert bus_def.direct_connection is True
    assert bus_def.is_addressable is True
    assert bus_def.max_initiators == "1"
    assert bus_def.max_targets is None
    assert bus_def.broadcast is None


def test_bus_definition_system_group_names():
    bus_def = parse_file(FIXTURE)
    assert bus_def.system_group_names == ["debug"]
