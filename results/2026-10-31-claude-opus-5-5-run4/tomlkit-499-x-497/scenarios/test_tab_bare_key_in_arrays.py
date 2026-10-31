import pytest

import tomlkit
from tomlkit.exceptions import ParseError


def test_tab_in_inline_table_key_inside_comma_first_array_rejected() -> None:
    content = "a = [\n  {p = 1} # c\n ,{q\tr = 2}\n]\n"
    with pytest.raises(ParseError):
        tomlkit.parse(content)

    with pytest.raises(ParseError):
        tomlkit.parse("a = [{x\ty = 1}]\n")


def test_tab_in_aot_header_and_value_helper_rejected() -> None:
    with pytest.raises(ParseError):
        tomlkit.parse("[[p\tq]]\nx = 1\n")

    with pytest.raises(ParseError):
        tomlkit.value("[{a\tb = 1}]")
