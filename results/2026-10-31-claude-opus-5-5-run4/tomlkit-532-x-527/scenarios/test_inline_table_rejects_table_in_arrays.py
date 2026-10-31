import pytest

import tomlkit

from tomlkit.items import InlineTable


def _table() -> object:
    t = tomlkit.table()
    t.append("k", 1)
    return t


def test_parsed_inline_tables_in_array_reject_table_children() -> None:
    content = "a = [{x = 1}, {y = 2}]\n"
    doc = tomlkit.parse(content)
    first = doc["a"][0]
    second = doc["a"][1]
    assert isinstance(first, InlineTable)
    assert isinstance(second, InlineTable)

    with pytest.raises(ValueError, match="cannot contain a table"):
        first.append("t", _table())
    with pytest.raises(ValueError, match="cannot contain a table"):
        second["t"] = _table()

    # rejection must not leave a partial mutation behind
    assert doc.as_string() == content
    assert tomlkit.parse(doc.as_string()) == {"a": [{"x": 1}, {"y": 2}]}


def test_array_built_from_string_rejects_table_but_accepts_dict() -> None:
    arr = tomlkit.array("[{a = 1}]")
    inline = arr[0]
    assert isinstance(inline, InlineTable)

    with pytest.raises(ValueError, match="cannot contain a table"):
        inline["t"] = _table()
    with pytest.raises(ValueError, match="cannot contain a table"):
        inline.setdefault("u", _table())

    assert "t" not in inline
    assert "u" not in inline
    assert arr.as_string() == "[{a = 1}]"

    # a plain dict is converted to a nested inline table and is allowed
    inline["n"] = {"x": 1}
    assert isinstance(inline["n"], InlineTable)
    doc = tomlkit.document()
    doc["arr"] = arr
    rendered = doc.as_string()
    assert tomlkit.parse(rendered) == {"arr": [{"a": 1, "n": {"x": 1}}]}
