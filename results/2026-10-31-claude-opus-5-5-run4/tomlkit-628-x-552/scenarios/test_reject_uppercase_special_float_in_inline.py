import pytest

import tomlkit
from tomlkit import parse
from tomlkit.exceptions import ParseError


@pytest.mark.parametrize(
    "content",
    [
        "v = [{a = {x = +NaN}, b = 1}]",
        "v = [[{a = {x = 1}, b = -Inf}]]",
        "v = [{a = {x = -INF}, b = 2}, 's']",
    ],
)
def test_uppercase_signed_special_floats_rejected_in_inline_tables(content: str) -> None:
    with pytest.raises(ParseError):
        parse(content)


def test_value_api_rejects_uppercase_signed_special_float_in_array() -> None:
    with pytest.raises(ParseError):
        tomlkit.value("[{a = {x = 1}, b = +Nan}]")
    ok = tomlkit.value("[{a = {x = +nan}, b = -inf}]")
    assert ok[0]["b"] == float("-inf")
