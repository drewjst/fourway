import math

import tomlkit


def test_numeric_fragments_merge_and_round_trip() -> None:
    content = "a.b.x = 0xff\na.b.y = 1e3\na.b.z = 3.25\na.b.w = 42\n"
    doc = tomlkit.parse(content)
    assert doc.as_string() == content
    assert doc.unwrap() == {"a": {"b": {"x": 255, "y": 1000.0, "z": 3.25, "w": 42}}}
    b = doc["a"]["b"]
    assert b["x"] == 255
    assert b["y"] == 1000.0
    assert isinstance(b["y"], float)


def test_special_floats_in_fragments_survive() -> None:
    content = "a.b.e = inf\na.b.f = -inf\na.b.g = nan\n"
    doc = tomlkit.parse(content)
    assert doc.as_string() == content
    b = doc["a"]["b"]
    assert b["e"] == float("inf")
    assert b["f"] == float("-inf")
    assert math.isnan(b["g"])
    merged = doc["a"].value
    assert merged["b"]["e"] == float("inf")
    assert math.isnan(merged["b"]["g"])
