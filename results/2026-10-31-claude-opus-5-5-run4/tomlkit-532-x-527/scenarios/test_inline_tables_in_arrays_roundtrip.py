import pytest

import tomlkit


@pytest.mark.parametrize(
    "content",
    [
        "a = [{b.c = 1}, {d = [{e = 2}]},]\n",
        "a = [ {x = 1} , { y = { z = 3 } } ]\n",
        "a = [\n  {x = 1}, # c\n  {y = 2},\n]\n",
        "a = []\nb = [ ]\n",
    ],
)
def test_valid_arrays_of_inline_tables_round_trip(content: str) -> None:
    doc = tomlkit.parse(content)
    assert doc.as_string() == content


def test_dump_and_edit_nested_inline_tables_in_arrays() -> None:
    data = {"x": [[{"a": {"b": 1}}]], "y": {"z": [[{"c": {"d": [1, 2]}}]]}}
    rendered = tomlkit.dumps(data)
    loaded = tomlkit.loads(rendered)
    assert loaded == data
    assert loaded.as_string() == rendered

    doc = tomlkit.parse("a = [{b.c = 1}, {d = 2}]\n")
    doc["a"][1]["e"] = {"x": 1}
    doc["a"][0]["b"]["f"] = 3
    out = doc.as_string()
    reparsed = tomlkit.parse(out)
    assert reparsed == {"a": [{"b": {"c": 1, "f": 3}}, {"d": 2, "e": {"x": 1}}]}
    assert reparsed.as_string() == out
