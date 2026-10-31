import datetime

import tomlkit
from tomlkit import parse


def test_appending_quote_and_backslash_round_trips_in_document():
    doc = parse('s = "foo"\nb = "bar"\nt = 07:32:00\n')
    doc["s"] += '"'
    doc["b"] += "\\"
    rendered = doc.as_string()
    reparsed = parse(rendered)
    assert reparsed["s"] == 'foo"'
    assert reparsed["b"] == "bar\\"
    assert reparsed["t"] == datetime.time(7, 32)
    assert parse(rendered).as_string() == rendered


def test_appending_to_multiline_basic_string_escapes_backslash():
    s = tomlkit.string("line", multiline=True)
    s += "\\end"
    assert s == "line\\end"
    assert parse(f"k = {s.as_string()}")["k"] == "line\\end"
