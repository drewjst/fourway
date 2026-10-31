import math

import tomlkit
from tomlkit import dumps, loads, parse, string


def test_dumps_esc_as_unicode_escape_alongside_floats():
    d = {
        "k\x1b": "a\x1bb",
        "m": string("x\x1by", multiline=True),
        "f": -0.5,
    }
    out = dumps(d)
    assert '"k\\u001b" = "a\\u001bb"' in out
    assert '"""x\\u001by"""' in out
    assert "\\e" not in out
    back = loads(out)
    assert back["k\x1b"] == "a\x1bb"
    assert back["m"] == "x\x1by"
    assert back["f"] == -0.5


def test_appending_esc_to_parsed_string_uses_unicode_escape():
    doc = parse('s = "a"\nx = -1.5\n')
    doc["s"] += "\x1b"
    doc["x"] *= 2
    out = doc.as_string()
    assert 's = "a\\u001b"' in out
    assert "\\e" not in out
    assert "x = -3.0" in out
    back = parse(out)
    assert back["s"] == "a\x1b"
    assert back["x"] == -3.0
