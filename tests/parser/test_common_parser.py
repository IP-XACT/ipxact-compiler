"""Unit tests for the low-level XML helpers in common_parser.py, in particular that text
content is stripped of surrounding whitespace. lxml returns element text verbatim,
including any indentation a pretty-printed or hand-edited file wraps around it; left
unstripped, that whitespace used to flow into enum construction (Direction(...),
Presence(...), ...) and raise ValueError on otherwise-valid input.
"""

from lxml import etree

from ipxact.parser.common_parser import elem_text, text, texts

NS = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"


def _parse(xml: str) -> etree._Element:
    return etree.fromstring(f'<root xmlns:ipxact="{NS}">{xml}</root>')


def test_elem_text_strips_surrounding_whitespace():
    root = _parse("<ipxact:direction>\n    in\n  </ipxact:direction>")
    assert elem_text(root.find(f"{{{NS}}}direction")) == "in"


def test_elem_text_returns_none_for_missing_element():
    assert elem_text(None) is None


def test_text_helper_strips_surrounding_whitespace():
    root = _parse("<ipxact:presence>\n    required\n  </ipxact:presence>")
    assert text(root, "presence") == "required"


def test_texts_helper_strips_each_item():
    root = _parse(
        "<ipxact:systemGroupName>\n  debug\n</ipxact:systemGroupName>"
        "<ipxact:systemGroupName>trace</ipxact:systemGroupName>"
    )
    assert texts(root, "systemGroupName") == ["debug", "trace"]
