from tomlkit import parse


def test_inline_deletions_under_dotted_key_render_identically():
    cases = [
        (("b",), "x.t = {a = 1,  c = 3}\ny = 2\n"),
        (("c",), "x.t = {a = 1, b = 2 }\ny = 2\n"),
        (("b", "c"), "x.t = {a = 1  }\ny = 2\n"),
    ]
    for dels, expected in cases:
        doc = parse("x.t = {a = 1, b = 2, c = 3}\ny = 2\n")
        for k in dels:
            del doc["x"]["t"][k]
        out = doc.as_string()
        assert out == expected
        assert parse(out).as_string() == out
        assert parse(out)["y"] == 2


def test_plain_table_replacement_preserves_inline_sibling():
    doc = parse("[a]\nx = 1\n\n[b]\nt = {p = 1, q = 2, r = 3}\n")
    doc["a"] = {"y": 2}
    del doc["b"]["t"]["q"]
    out = doc.as_string()
    reparsed = parse(out)
    assert reparsed == {"a": {"y": 2}, "b": {"t": {"p": 1, "r": 3}}}
    assert reparsed.as_string() == out
    assert "t = {p = 1,  r = 3}" in out
