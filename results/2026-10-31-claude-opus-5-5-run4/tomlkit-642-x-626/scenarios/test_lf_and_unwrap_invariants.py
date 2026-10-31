from datetime import datetime, timedelta, timezone

import pytest

from tomlkit import parse
from tomlkit.exceptions import UnexpectedCharError


def test_lf_document_error_position_unchanged() -> None:
    content = "a = 1979-05-27T07:32:00\nb = @\n"
    with pytest.raises(UnexpectedCharError) as e:
        parse(content)
    assert e.value.line == 2
    assert e.value.col == 4


def test_crlf_parsed_datetime_unwraps_to_plain_value() -> None:
    doc = parse("dt = 1979-05-27T07:32:00Z\r\nx = 1\r\n")
    out = doc.unwrap()
    assert type(out["dt"]) is datetime
    assert out["dt"].fold == 0
    assert out["dt"] == datetime(1979, 5, 27, 7, 32, tzinfo=timezone(timedelta()))
    assert out["x"] == 1
