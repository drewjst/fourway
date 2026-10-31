import math

from tomlkit import parse


def test_negative_zero_from_signed_float_next_to_esc_string():
    doc = parse('s = "a\\eb"\nx = -1.5\n')
    doc["x"] *= 0
    out = doc.as_string()
    assert "x = -0.0" in out
    assert "+-" not in out
    back = parse(out)
    assert back["x"] == 0.0
    assert math.copysign(1.0, back["x"]) == -1.0
    assert back["s"] == "a\x1bb"


def test_negative_zero_from_signed_int_division():
    doc = parse('n = +0\ns = "q"\n')
    doc["s"] += "\x1b"
    doc["n"] /= -1
    out = doc.as_string()
    assert "n = -0.0" in out
    back = parse(out)
    assert math.copysign(1.0, back["n"]) == -1.0
    assert back["s"] == "q\x1b"
