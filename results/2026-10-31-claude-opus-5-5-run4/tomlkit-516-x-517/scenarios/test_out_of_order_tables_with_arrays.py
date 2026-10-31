from tomlkit import parse


def test_new_sibling_subtable_with_arrays_parses_and_round_trips() -> None:
    content = "[a.b]\nx = [1, ]\n[a]\ny = []\n[a.c]\nz = [ ]\n"
    doc = parse(content)
    assert doc.value == {"a": {"b": {"x": [1]}, "y": [], "c": {"z": []}}}
    assert doc.as_string() == content


def test_extending_subtable_with_deeper_header_and_arrays_parses() -> None:
    content = "[a.b]\nx = []\n[a]\n[a.b.c]\nw = [1,]\n"
    doc = parse(content)
    assert doc.value == {"a": {"b": {"x": [], "c": {"w": [1]}}}}
