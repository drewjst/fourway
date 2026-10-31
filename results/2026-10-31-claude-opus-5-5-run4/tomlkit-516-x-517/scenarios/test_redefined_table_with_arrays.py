import pytest

from tomlkit import parse
from tomlkit.exceptions import ParseError


def test_redefined_subtable_with_value_less_array_closes_is_rejected() -> None:
    content = "[a.b]\nx = [1, ]\n[a]\ny = []\n[a.b]\nz = [ ]\n"
    with pytest.raises(ParseError):
        parse(content)


def test_deep_redefined_subtable_with_arrays_is_rejected() -> None:
    content = "[a.b.c]\nv = [[1, ], []]\n[a]\nw = [ ]\n[a.b.c]\nq = [2,]\n"
    with pytest.raises(ParseError):
        parse(content)
