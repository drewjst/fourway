import math

from tomlkit import dumps
from tomlkit import parse


def test_dumps_inline_tables_with_special_floats_reparse() -> None:
    data = {
        "x": {
            "y": [
                {"a": {"p": float("inf"), "q": float("-inf")}, "b": float("nan")},
                "s",
            ]
        }
    }
    text = dumps(data)
    doc = parse(text)
    first = doc["x"]["y"][0]
    assert set(first.keys()) == {"a", "b"}
    assert first["a"]["p"] == math.inf
    assert first["a"]["q"] == -math.inf
    assert math.isnan(first["b"])
    assert doc["x"]["y"][1] == "s"
    assert doc.as_string() == text


def test_parsed_lowercase_signed_specials_in_inline_tables_round_trip() -> None:
    content = "v = [{a = {x = +inf}, b = -nan}, {c = +nan}]\n"
    doc = parse(content)
    assert doc["v"][0]["a"]["x"] == math.inf
    assert math.isnan(doc["v"][0]["b"])
    assert dumps(doc) == content
