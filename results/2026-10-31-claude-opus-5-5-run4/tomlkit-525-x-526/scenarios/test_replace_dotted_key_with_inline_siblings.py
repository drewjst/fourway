import tomlkit
from tomlkit import parse


def test_dotted_replacement_keeps_edited_inline_sibling():
    doc = parse("a.b = 1\nc.d = {x = 1, y = 2, z = 3}\n")
    del doc["c"]["d"]["y"]
    doc["a"] = {"x": 9}

    out = doc.as_string()
    assert out == "c.d = {x = 1,  z = 3}\n\n[a]\nx = 9\n"
    reparsed = parse(out)
    assert reparsed == {"c": {"d": {"x": 1, "z": 3}}, "a": {"x": 9}}
    assert reparsed.as_string() == out


def test_dotted_replacement_with_table_holding_inline_table():
    doc = parse("a.b = 1\nc.d = 2\n")
    t = tomlkit.inline_table()
    t["p"] = 1
    t["q"] = 2
    doc["a"] = {"t": t}

    out = doc.as_string()
    assert out == "c.d = 2\n\n[a]\nt = {p = 1, q = 2}\n"
    assert parse(out) == {"c": {"d": 2}, "a": {"t": {"p": 1, "q": 2}}}

    del doc["a"]["t"]["q"]
    out = doc.as_string()
    assert out == "c.d = 2\n\n[a]\nt = {p = 1}\n"
    assert parse(out) == {"c": {"d": 2}, "a": {"t": {"p": 1}}}
    assert parse(out).as_string() == out
