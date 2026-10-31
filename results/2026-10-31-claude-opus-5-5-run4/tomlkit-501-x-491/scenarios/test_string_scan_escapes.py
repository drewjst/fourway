import pytest

from tomlkit import parse
from tomlkit.exceptions import InvalidControlChar
from tomlkit.exceptions import UnexpectedEofError


def test_valid_escapes_between_long_runs_decode_and_round_trip():
    run = "some ordinary text " * 10
    content = (
        'a = "' + run + '\\u00e9 mid \\U0001F600 tail \\u00C9\\t end' + run + '"\n'
        "b = 'lit \\u12_3 raw'\n"
        '[t]\n"k\\u0041y" = "v\\u0042w"\n'
    )
    doc = parse(content)
    assert doc["a"] == run + "\u00e9 mid \U0001F600 tail \u00c9\t end" + run
    assert doc["b"] == "lit \\u12_3 raw"
    assert doc["t"]["kAy"] == "vBw"
    assert doc.as_string() == content


def test_error_types_after_escape_are_preserved():
    with pytest.raises(InvalidControlChar):
        parse('a = "abc\\u0041\x01def"')
    with pytest.raises(InvalidControlChar):
        parse('a = "abc\\u0041def\x7fghi"')
    with pytest.raises(UnexpectedEofError):
        parse('a = "abc\\u0041defghijkl')
    assert parse('a = "\\u0041\tb"')["a"] == "A\tb"
