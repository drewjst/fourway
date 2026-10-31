from tomlkit import parse


CONTENT = "[[a.b.c]]\nx = 1\n[a]\nb.z = 1\n"


def test_super_table_with_aot_extended_by_dotted_key_round_trips() -> None:
    doc = parse(CONTENT)
    assert doc.unwrap() == {"a": {"b": {"c": [{"x": 1}], "z": 1}}}
    assert doc.as_string() == CONTENT


def test_emptying_aot_in_dotted_extended_super_table_keeps_valid_toml() -> None:
    doc = parse(CONTENT)
    aot = doc["a"]["b"]["c"]
    assert len(aot) == 1
    aot.pop()
    assert len(aot) == 0

    out = doc.as_string()
    # The re-rendered document must still be parseable TOML and must keep
    # the dotted-key extension of the super table.
    reparsed = parse(out)
    assert reparsed["a"]["b"]["z"] == 1
