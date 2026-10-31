import pytest

from tomlkit import parse
from tomlkit.exceptions import ParseError


def test_dotted_inline_table_then_out_of_order_table_header_rejected() -> None:
    content = "[a]\nb.c = {}\n[zz]\nq = 9\n[a.b]\nd = 2\n"
    with pytest.raises(ParseError):
        parse(content)


def test_inline_table_value_then_out_of_order_table_header_rejected() -> None:
    content = "[a]\nb = {}\n[zz]\nq = 9\n[a.b]\nc = 1\n"
    with pytest.raises(ParseError):
        parse(content)
