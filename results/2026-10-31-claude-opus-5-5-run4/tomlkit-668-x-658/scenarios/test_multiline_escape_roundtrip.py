import tomlkit
from tomlkit import parse


def test_default_escape_multiline_leading_newline_round_trips() -> None:
    for kwargs in ({"multiline": True}, {"multiline": True, "literal": True}):
        for value in ("\nMy\nString", "\r\nMy\nString"):
            s = tomlkit.string(value, **kwargs)
            assert str(s) == value
            assert str(parse(f"k = {s.as_string()}\n")["k"]) == value


def test_default_escape_multiline_basic_bare_cr_escaped() -> None:
    s = tomlkit.string("My\rString", multiline=True)
    assert s.as_string() == '"""My\\rString"""'
    assert str(parse(f"k = {s.as_string()}\n")["k"]) == "My\rString"
    q = tomlkit.string('a"b')
    assert q.as_string() == '"a\\"b"'
