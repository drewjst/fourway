import pytest

from tomlkit import parse
from tomlkit.exceptions import InvalidUnicodeValueError


LONG = "lorem ipsum dolor sit amet " * 20


@pytest.mark.parametrize(
    "escape",
    [r"\u12_3", r"\u+123", r"\u 123", r"\u1_23", r"\U0010_FFFF", r"\U0000_0041"],
)
def test_invalid_unicode_escape_inside_long_single_line_string(escape):
    content = 'a = "' + LONG + escape + LONG + '"\n'
    with pytest.raises(InvalidUnicodeValueError):
        parse(content)


@pytest.mark.parametrize(
    "content",
    [
        r'"key \u12_3 name" = 1',
        '[table]\n"abc\\u+123def" = "x"\n',
        r'["prefix\u1_23suffix"]' + "\nx = 1\n",
        r'a = {b = "value text \u 123 more text"}',
        r'a = ["first plain", "second \U0000_0041 tail"]',
        r'a = "ok \u00e9 text"' + "\n" + r'b = "bad text \u12_3"',
    ],
)
def test_invalid_unicode_escape_in_keys_and_nested_values(content):
    with pytest.raises(InvalidUnicodeValueError):
        parse(content)
