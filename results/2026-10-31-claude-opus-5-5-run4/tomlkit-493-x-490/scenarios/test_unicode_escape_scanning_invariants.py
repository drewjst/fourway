import datetime

import pytest

from tomlkit import parse
from tomlkit.exceptions import InvalidUnicodeValueError


def test_boundary_big_u_escapes_parse_and_round_trip() -> None:
    content = (
        r'  "\U0000D7FF"   =   "\U0000E000"  # c'
        + "\n"
        + r'k = "\uD7FF|\uE000"'
        + "\n"
        + "n =   1_000\n"
    )
    doc = parse(content)
    assert doc["\ud7ff"] == "\ue000"
    assert doc["k"] == "\ud7ff|\ue000"
    assert doc["n"] == 1000
    assert doc.as_string() == content


def test_astral_big_u_escape_in_table_header_and_following_values() -> None:
    content = (
        r'["\U0001F600".x]'
        + "\n"
        + "n = 1_000\n"
        + "d = 1979-05-27 07:32:00\n"
        + r'  s   =   "\U0010FFFF"   # tail'
        + "\n"
    )
    doc = parse(content)
    tbl = doc["\U0001F600"]["x"]
    assert tbl["n"] == 1000
    assert tbl["d"] == datetime.datetime(1979, 5, 27, 7, 32, 0)
    assert tbl["s"] == "\U0010FFFF"
    assert doc.as_string() == content


@pytest.mark.parametrize(
    "content",
    [
        r'a = "\U0000GGGG"',
        r'  "\U0000ZZ00"  = 1',
        r'"\uD800" = 1',
        r'   a  =  "\uDFFF"   # c',
        r't = { k = "\uDC00" }',
    ],
)
def test_invalid_and_short_surrogate_escapes_still_rejected(content: str) -> None:
    with pytest.raises(InvalidUnicodeValueError):
        parse(content)
