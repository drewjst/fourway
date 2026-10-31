from tomlkit import parse

CONTENT = "[a]\nx.y = {}\n[zz]\nq = 9\n[a.b]\nc = 1\n"


def test_valid_out_of_order_with_dotted_inline_table_round_trips() -> None:
    doc = parse(CONTENT)
    assert doc.as_string() == CONTENT
    assert doc.unwrap() == {
        "a": {"x": {"y": {}}, "b": {"c": 1}},
        "zz": {"q": 9},
    }


def test_adding_key_to_valid_out_of_order_table_reparses() -> None:
    doc = parse(CONTENT)
    doc["a"]["z"] = 2
    out = doc.as_string()
    assert parse(out).unwrap() == {
        "a": {"x": {"y": {}}, "z": 2, "b": {"c": 1}},
        "zz": {"q": 9},
    }
