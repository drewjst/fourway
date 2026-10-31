import tomlkit


def test_repr_merges_float_and_special_float_fragments() -> None:
    doc = tomlkit.parse("a.b.c = 1.5\na.b.e = inf\na.b.f = -inf\na.b.g = nan\n")
    expected = "{'b': {'c': 1.5, 'e': inf, 'f': -inf, 'g': nan}}"
    assert repr(doc["a"]) == expected
    assert str(doc["a"]) == expected


def test_repr_merges_hex_int_and_exponent_float_fragments() -> None:
    doc = tomlkit.parse("a.b.x = 0xff\na.b.y = 1e3\na.b.z = +12\n")
    expected = "{'b': {'x': 255, 'y': 1000.0, 'z': 12}}"
    assert repr(doc["a"]) == expected
    assert str(doc["a"]) == expected
