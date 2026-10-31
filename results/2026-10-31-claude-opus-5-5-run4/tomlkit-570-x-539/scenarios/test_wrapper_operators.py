import tomlkit
from tomlkit.items import Array, Table


def test_array_iadd_keeps_wrapper_and_renders() -> None:
    arr = tomlkit.array()
    arr.extend([1, 2])
    original = id(arr)
    arr += [3]
    assert isinstance(arr, Array)
    assert id(arr) == original
    assert arr == [1, 2, 3]
    assert arr.as_string() == "[1, 2, 3]"
    combined = arr + [4]
    assert list(combined) == [1, 2, 3, 4]


def test_table_or_returns_new_table_and_ior_in_place() -> None:
    table = tomlkit.table()
    table["a"] = 1
    result = table | {"b": 2}
    assert isinstance(result, Table)
    assert result is not table
    assert dict(result) == {"a": 1, "b": 2}
    original = id(table)
    table |= {"c": 3}
    assert id(table) == original
    assert dict(table) == {"a": 1, "c": 3}
