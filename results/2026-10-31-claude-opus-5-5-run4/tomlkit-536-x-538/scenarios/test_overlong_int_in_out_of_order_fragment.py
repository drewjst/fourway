import sys

import pytest

import tomlkit
from tomlkit.exceptions import InvalidNumberError
from tomlkit.items import Integer


pytestmark = pytest.mark.skipif(
    not hasattr(sys, "get_int_max_str_digits"),
    reason="requires the int-from-string digit limit",
)


@pytest.fixture(autouse=True)
def _default_limit():
    old = sys.get_int_max_str_digits()
    sys.set_int_max_str_digits(4300)
    try:
        yield
    finally:
        sys.set_int_max_str_digits(old)


def test_overlong_integer_in_second_dotted_fragment_is_rejected() -> None:
    content = "a.b.c = 1.5\na.b.e = " + "9" * 4301 + "\n"
    with pytest.raises(InvalidNumberError):
        tomlkit.parse(content)


def test_integer_under_limit_in_fragment_stays_integer() -> None:
    big = "9" * 4300
    doc = tomlkit.parse("a.b.c = 1.5\na.b.e = " + big + "\n")
    value = doc["a"]["b"]["e"]
    assert isinstance(value, Integer)
    assert value == int(big)
    assert doc["a"]["b"]["c"] == 1.5
