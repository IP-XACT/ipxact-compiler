"""Regression tests for object-model gaps found while building an external SystemVerilog
importer on top of this library (see GitHub issue #2): StructuredPort's missing
structPortTypeDefs, PortMap's missing physicalPort/subPort, Port's missing arrays, and
VLNV.parse()'s unhelpful error on malformed input.
"""

from pathlib import Path

import pytest

from ipxact.parser.main_parser import parse_file
from ipxact.schema.common import ArrayBound, SubPortReference
from ipxact.schema.ports import Direction
from ipxact.schema.vlnv import VLNV

FIXTURE = Path(__file__).parent / "xml" / "struct_port.xml"


def test_structured_port_type_defs():
    component = parse_file(FIXTURE)
    apb_req = component.model.ports[0]
    assert apb_req.structured.struct_type == "struct"
    assert apb_req.structured.direction is Direction.OUT

    type_def = apb_req.structured.struct_port_type_defs[0]
    assert type_def.type_name == "apb_req_t"
    assert type_def.constrained == ["WIDTH", "DEPTH"]
    assert type_def.type_definitions == ["apb_pkg.sv"]
    assert type_def.type_parameters[0].name == "WIDTH"
    assert type_def.type_parameters[0].value == "32"
    assert type_def.view_refs == ["rtl"]


def test_structured_port_sub_port_arrays():
    """Regression test: subPortType has the same optional <ipxact:arrays> as portType
    (port.xsd), but only Port.arrays was added at first; SubPort.arrays was missing.
    """
    component = parse_file(FIXTURE)
    apb_req = component.model.ports[0]
    sub_port = apb_req.structured.sub_ports[0]
    assert sub_port.arrays == [ArrayBound(left="0", right="3", array_id=None)]


def test_port_map_sub_port_refs():
    component = parse_file(FIXTURE)
    port_map = component.bus_interfaces[0].abstraction_types[0].port_maps[0]
    assert port_map.physical_port == "apb_req"
    assert port_map.sub_port_refs == [SubPortReference(sub_port_ref="pwdata", part_select=None)]


def test_port_map_physical_port_part_select():
    """Regression test: physicalPort's own <partSelect> (a sibling of subPort, used when
    referencing a bit range directly instead of via named subPorts) had no field on
    PortMap and was silently dropped.
    """
    component = parse_file(FIXTURE)
    port_map = component.bus_interfaces[0].abstraction_types[0].port_maps[0]
    assert port_map.part_select is not None
    assert port_map.part_select.range_left == "7"
    assert port_map.part_select.range_right == "0"


def test_port_arrays():
    component = parse_file(FIXTURE)
    mem = component.model.ports[1]
    assert mem.arrays == [ArrayBound(left="0", right="15", array_id=None)]


def test_vlnv_parse_raises_clear_error_on_malformed_input():
    with pytest.raises(ValueError, match="expected a 'vendor:library:name:version' string"):
        VLNV.parse("not-a-valid-vlnv")
