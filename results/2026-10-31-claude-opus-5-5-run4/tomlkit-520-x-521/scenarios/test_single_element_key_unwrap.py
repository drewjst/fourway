import tomlkit
from tomlkit.items import Item


def test_single_element_key_is_visible_and_unwraps() -> None:
    doc = tomlkit.document()
    doc.append(tomlkit.key(["foo"]), "value")
    doc.append(tomlkit.key(["a", "b"]), 1)

    assert "foo" in doc
    assert doc["foo"] == "value"

    unwrapped = doc.unwrap()
    assert unwrapped == {"foo": "value", "a": {"b": 1}}
    assert list(unwrapped.keys()) == ["foo", "a"]
    assert type(unwrapped["foo"]) is str
    assert all(type(k) is str for k in unwrapped)
    assert not isinstance(unwrapped["a"], Item)

    # The rendered document round-trips to the same plain data.
    assert tomlkit.parse(doc.as_string()).unwrap() == unwrapped


def test_single_element_key_table_unwraps() -> None:
    doc = tomlkit.document()
    doc.append(tomlkit.key(["outer"]), {"inner": 1})

    assert "outer" in doc
    outer = doc["outer"]
    assert outer.unwrap() == {"inner": 1}

    unwrapped = doc.unwrap()
    assert unwrapped == {"outer": {"inner": 1}}
    assert type(unwrapped["outer"]) is dict
    assert type(unwrapped["outer"]["inner"]) is int
    assert doc.as_string() == "[outer]\ninner = 1\n"
