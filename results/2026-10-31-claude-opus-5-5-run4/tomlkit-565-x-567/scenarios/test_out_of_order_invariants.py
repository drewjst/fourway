import pytest

from tomlkit import parse
from tomlkit.exceptions import ParseError


def test_concrete_table_redefined_by_dotted_key_is_rejected() -> None:
    with pytest.raises(ParseError):
        parse("[a.b]\n[a]\nb.z = 1\n")


def test_non_empty_aot_under_reopened_super_table_round_trips() -> None:
    content = "[[a.b.c]]\nx = 1\n[a]\ny = 1\n"
    doc = parse(content)
    assert doc.as_string() == content
    assert doc.unwrap() == {"a": {"b": {"c": [{"x": 1}]}, "y": 1}}
