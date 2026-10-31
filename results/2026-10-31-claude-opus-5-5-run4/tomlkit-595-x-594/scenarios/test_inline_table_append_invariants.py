import tomlkit
from tomlkit import parse


def test_padded_inline_table_append_from_key_value_is_not_double_spaced() -> None:
    doc = parse("a = { foo = 1, bar = 2 }\n")
    _, v = tomlkit.key_value("baz = 3\n")
    doc["a"]["baz"] = v

    rendered = doc.as_string()
    assert rendered == "a = { foo = 1, bar = 2, baz = 3}\n"
    assert parse(rendered) == {"a": {"foo": 1, "bar": 2, "baz": 3}}


def test_sequential_key_value_appends_round_trip() -> None:
    doc = parse("a = {x = 1, y = 2}\n")
    sources = {"p": "p = 10", "q": "q = 11\n", "r": "r = 12  ", "s": "s = 13 \n"}
    for name, src in sources.items():
        k, v = tomlkit.key_value(src)
        assert k.key == name
        doc["a"][name] = v

    rendered = doc.as_string()
    assert ",," not in rendered
    assert ", ," not in rendered
    reparsed = parse(rendered)
    assert reparsed == {
        "a": {"x": 1, "y": 2, "p": 10, "q": 11, "r": 12, "s": 13}
    }
    assert reparsed.as_string() == rendered
