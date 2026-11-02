"""Validation against the IEEE 1685-2022 XSD shipped in src/ipxact/xsd/."""

from pathlib import Path

import pytest
from lxml import etree

import ipxact

FIXTURES = sorted((Path(__file__).parent / "parser" / "xml").glob("*.xml"))
APB_UART = Path(__file__).parent / "parser" / "xml" / "apb_uart.xml"


def _write(tmp_path: Path, source: str) -> Path:
    path = tmp_path / "doc.xml"
    path.write_text(source)
    return path


@pytest.mark.parametrize("fixture", FIXTURES, ids=lambda p: p.name)
def test_fixtures_are_valid(fixture):
    assert ipxact.validate(fixture) == []


def test_duplicate_parameter_id_is_reported(tmp_path):
    source = APB_UART.read_text()
    start = source.index("<ipxact:parameter ")
    end = source.index("</ipxact:parameter>") + len("</ipxact:parameter>")
    doubled = source[:end] + "\n    " + source[start:end] + source[end:]
    path = _write(tmp_path, doubled)

    issues = ipxact.validate(path)
    assert len(issues) == 1
    assert "Duplicate key-sequence ['BAUD_RATE']" in issues[0].message
    # reported on the second <ipxact:parameter>
    assert issues[0].line == doubled[: doubled.index("<ipxact:parameter ", end)].count("\n") + 1


def test_parse_file_validate_raises_on_invalid_file(tmp_path):
    path = _write(tmp_path, APB_UART.read_text().replace("<ipxact:name>apb_uart</ipxact:name>", "", 1))

    with pytest.raises(ipxact.ValidationError) as error:
        ipxact.parse_file(path, validate=True)
    assert error.value.issues
    assert "version" in error.value.issues[0].message

    # Without validate, the same file still parses (with an empty name).
    assert ipxact.parse_file(path).vlnv.name == ""


def test_parse_file_validate_accepts_valid_file():
    assert ipxact.parse_file(APB_UART, validate=True).vlnv.name == "apb_uart"


def test_validate_accepts_a_parsed_tree():
    root = etree.parse(str(APB_UART)).getroot()
    assert ipxact.validate(root) == []
    etree.SubElement(root, "{http://www.accellera.org/XMLSchema/IPXACT/1685-2022}notAnElement")
    assert ipxact.validate(root)


def test_xsd_files_are_shipped():
    folder = ipxact.xsd_path()
    assert len(list(folder.glob("*.xsd"))) == 24
    assert (folder / "index.xsd").is_file()
    assert (folder / "LICENSE").is_file()
