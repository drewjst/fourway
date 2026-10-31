import pytest

import tomlkit

from tomlkit.exceptions import ParseError
from tomlkit.exceptions import UnexpectedCharError


@pytest.mark.parametrize(
    "content",
    [
        "a = {x = [{1]}\n",
        "a = {x = [{y = 1}, {z]}\n",
        "a = [{p = [{q]}]\n",
    ],
)
def test_malformed_inline_table_inside_nested_array_raises(content: str) -> None:
    with pytest.raises(UnexpectedCharError):
        tomlkit.parse(content)


def test_value_and_array_helpers_reject_malformed_inline_table_element() -> None:
    with pytest.raises(ParseError):
        tomlkit.array("[{a]")
    with pytest.raises(ParseError):
        tomlkit.value("[{a = 1}, {b]")
    with pytest.raises(ParseError):
        tomlkit.array("[[1, {x]]")
