import math

import tomlkit
from tomlkit import parse


def test_item_inline_table_order_with_special_floats_round_trips() -> None:
    value = [[{"a": {"x": float("inf")}, "b": float("-inf")}]]
    rendered = tomlkit.item(value).as_string().strip()
    assert rendered == "[[{a = {x = inf}, b = -inf}]]"

    doc = parse("v = " + rendered + "\n")
    inner = doc["v"][0][0]
    assert list(inner.keys()) == ["a", "b"]
    assert inner["a"]["x"] == math.inf
    assert inner["b"] == -math.inf
    assert doc.as_string() == "v = " + rendered + "\n"


def test_item_mixed_array_inline_table_order_with_nan() -> None:
    value = [{"a": {"x": float("nan")}, "b": float("inf")}, "s"]
    rendered = tomlkit.item(value).as_string()
    assert rendered == '[{a = {x = nan}, b = inf}, "s"]'

    doc = parse("v = " + rendered)
    first = doc["v"][0]
    assert list(first.keys()) == ["a", "b"]
    assert math.isnan(first["a"]["x"])
    assert first["b"] == math.inf
