from datetime import datetime, timedelta

import tomlkit
from tomlkit.items import item


def test_integer_string_preserves_underscores() -> None:
    n = tomlkit.integer("1_000")
    assert n.as_string() == "1_000"
    assert int(n) == 1000
    h = tomlkit.integer("0xdead_beef")
    assert h.as_string() == "0xdead_beef"
    assert int(h) == 0xDEADBEEF


def test_grouped_integer_dumps_alongside_datetime_arithmetic() -> None:
    doc = tomlkit.document()
    doc["n"] = tomlkit.integer("5_349_221")
    doc["dt"] = item(datetime(2018, 7, 22, 12, 34, 56)) - timedelta(days=1)
    out = tomlkit.dumps(doc)
    assert "n = 5_349_221\n" in out
    assert "dt = 2018-07-21T12:34:56" in out
    reparsed = tomlkit.parse(out)
    assert reparsed["n"] == 5349221
    assert reparsed["n"].as_string() == "5_349_221"
    assert reparsed["dt"] == datetime(2018, 7, 21, 12, 34, 56)
