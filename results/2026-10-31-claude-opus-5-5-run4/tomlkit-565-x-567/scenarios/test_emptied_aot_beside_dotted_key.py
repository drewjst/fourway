from tomlkit import parse


def test_emptied_child_aot_coexists_with_dotted_key() -> None:
    doc = parse("[a]\nb.z = 1\n\n[[a.d]]\nx = 1\n")
    doc["a"]["d"].pop()

    out = doc.as_string()
    reparsed = parse(out)
    assert reparsed.unwrap() == {"a": {"b": {"z": 1}, "d": []}}
    assert out.startswith("[a]\n")
