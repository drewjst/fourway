import pytest

import tomlkit
from tomlkit.exceptions import InvalidStringError


def test_lone_cr_escaped_in_multiline_basic_and_round_trips() -> None:
    s = tomlkit.string("My\rString", multiline=True)
    assert s.as_string() == '"""My\\rString"""'
    doc = tomlkit.document()
    doc["k"] = s
    reparsed = tomlkit.parse(doc.as_string())
    assert reparsed["k"] == "My\rString"


def test_lone_cr_in_array_of_multiline_strings_round_trips() -> None:
    arr = tomlkit.array()
    arr += [tomlkit.string("\rlead", multiline=True)]
    rendered = "a = " + arr.as_string() + "\n"
    assert tomlkit.parse(rendered)["a"] == ["\rlead"]


def test_lone_cr_rejected_in_multiline_literal() -> None:
    with pytest.raises(InvalidStringError):
        tomlkit.string("My\rString", multiline=True, literal=True)
    with pytest.raises(InvalidStringError):
        tomlkit.string("a\r\nb\rc", multiline=True, literal=True)
