import io
import logging

import dotenv
from dotenv.parser import parse_stream


def test_crlf_invalid_line_warning_line_numbers(caplog):
    caplog.set_level(logging.WARNING, logger="dotenv.main")

    result = dotenv.dotenv_values(stream=io.StringIO("a: b\r\nc=d\r\ne: f"))

    assert result == {"c": "d"}
    assert caplog.messages == [
        "python-dotenv could not parse statement starting at line 1",
        "python-dotenv could not parse statement starting at line 3",
    ]


def test_crlf_invalid_line_consumes_whole_newline():
    bindings = list(parse_stream(io.StringIO("a: b\r\nc=d")))

    assert [b.original.string for b in bindings] == ["a: b\r\n", "c=d"]
    assert [b.error for b in bindings] == [True, False]
    assert bindings[1].key == "c" and bindings[1].value == "d"
