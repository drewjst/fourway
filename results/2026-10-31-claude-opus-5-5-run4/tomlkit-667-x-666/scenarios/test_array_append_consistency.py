from decimal import Decimal

import tomlkit
from tomlkit.exceptions import ConvertError
from tomlkit.items import Null


def _expected_map(array):
    return dict(
        enumerate(
            i
            for i, g in enumerate(array._value)
            if g.value is not None and not isinstance(g.value, Null)
        )
    )


def test_appends_to_commented_array_stay_consistent() -> None:
    doc = tomlkit.parse("x = [\n  1, # one\n  # lone comment\n  2,\n]\n")
    array = doc["x"]
    expected = [1, 2]
    for v in ["a", 3, True, "b"]:
        array.append(v)
        expected.append(v)
        assert array._index_map == _expected_map(array)
    array[-1] = "z"
    expected[-1] = "z"
    array[2] = "A"
    expected[2] = "A"
    assert array == expected
    out = doc.as_string()
    assert "# one" in out and "# lone comment" in out
    assert tomlkit.parse(out)["x"] == expected
    del array[0]
    expected.pop(0)
    array.append(9)
    expected.append(9)
    assert array._index_map == _expected_map(array)
    assert tomlkit.parse(doc.as_string())["x"] == expected


def test_custom_encoder_values_appended_to_array() -> None:
    def encode_decimal(obj):
        if isinstance(obj, Decimal):
            return tomlkit.float_(str(obj))
        raise ConvertError("not a decimal")

    tomlkit.register_encoder(encode_decimal)
    try:
        doc = tomlkit.document()
        doc["vals"] = tomlkit.array()
        arr = doc["vals"]
        for d in ["1.5", "2.25", "3.0"]:
            arr.append(Decimal(d))
        assert arr._index_map == _expected_map(arr)
        arr[1] = Decimal("9.5")
        assert tomlkit.parse(doc.as_string())["vals"] == [1.5, 9.5, 3.0]
    finally:
        tomlkit.unregister_encoder(encode_decimal)
