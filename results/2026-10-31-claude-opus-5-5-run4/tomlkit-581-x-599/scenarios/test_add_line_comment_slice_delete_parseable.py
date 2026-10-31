import tomlkit
from tomlkit import api


def _commented_array():
    a = api.array()
    a.add_line(1, 2, comment="c")
    return a


def test_slice_deletions_on_commented_array_render_parseable() -> None:
    a = _commented_array()
    del a[:-1]
    assert list(a) == [2]
    # the rendered array must still be valid TOML (bracket not on the comment line)
    tomlkit.parse("a = " + a.as_string() + "\n")

    b = _commented_array()
    del b[:0]
    assert list(b) == [1, 2]
    tomlkit.parse("a = " + b.as_string() + "\n")


def test_commented_array_in_document_after_prefix_slice_delete_dumps_valid() -> None:
    doc = tomlkit.document()
    a = _commented_array()
    del a[:-1]
    doc["a"] = a
    out = tomlkit.dumps(doc)
    reparsed = tomlkit.parse(out)
    assert "a" in reparsed
