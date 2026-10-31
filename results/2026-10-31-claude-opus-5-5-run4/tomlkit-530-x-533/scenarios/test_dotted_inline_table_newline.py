from tomlkit import parse


def test_add_key_after_dotted_inline_table_in_later_table() -> None:
    doc = parse("[zz]\nq = 9\n[x]\na.b = {}")
    doc["x"]["c"] = 3
    out = doc.as_string()
    assert out == "[zz]\nq = 9\n[x]\na.b = {}\nc = 3\n"
    assert parse(out).unwrap() == {"zz": {"q": 9}, "x": {"a": {"b": {}}, "c": 3}}


def test_add_key_after_dotted_inline_table_in_out_of_order_subtable() -> None:
    doc = parse("[x]\nk = 1\n[zz]\n[x.y]\na.b = {}")
    doc["x"]["y"]["c"] = 3
    out = doc.as_string()
    assert out == "[x]\nk = 1\n[zz]\n[x.y]\na.b = {}\nc = 3\n"
    assert parse(out).unwrap() == {
        "x": {"k": 1, "y": {"a": {"b": {}}, "c": 3}},
        "zz": {},
    }
