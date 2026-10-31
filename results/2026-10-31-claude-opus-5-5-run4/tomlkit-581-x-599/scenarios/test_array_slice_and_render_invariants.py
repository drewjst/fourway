import tomlkit
from tomlkit import item


def test_plain_single_line_array_positive_slice_delete_stays_single_line() -> None:
    a = item([1, 2, 3, 4])
    del a[1:3]
    assert list(a) == [1, 4]
    s = a.as_string()
    assert "\n" not in s
    assert s == "[1, 4]"
    assert tomlkit.parse("a = " + s)["a"] == [1, 4]


def test_parsed_multiline_array_with_comment_round_trips_after_slice_delete() -> None:
    doc = tomlkit.parse("a = [\n  1,\n  2, # two\n]\n")
    del doc["a"][0:1]
    assert list(doc["a"]) == [2]
    out = tomlkit.dumps(doc)
    reparsed = tomlkit.parse(out)
    assert reparsed["a"] == [2]
    assert "# two" in out
    assert reparsed.as_string() == out
