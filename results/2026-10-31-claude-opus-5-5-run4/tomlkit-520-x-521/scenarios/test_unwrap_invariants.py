import pytest

import tomlkit
from tomlkit import parse
from tomlkit.exceptions import KeyAlreadyPresent
from tomlkit.items import Item


def _assert_plain(obj: object) -> None:
    assert not isinstance(obj, Item)
    if isinstance(obj, dict):
        assert type(obj) is dict
        for k, v in obj.items():
            assert type(k) is str
            _assert_plain(v)
    elif isinstance(obj, list):
        assert type(obj) is list
        for v in obj:
            _assert_plain(v)


def test_out_of_order_tables_unwrap_merged() -> None:
    doc = parse("[a.x]\np = 1\n[foo]\nbar = 2\n[a.y]\nq = 3\n")
    unwrapped = doc.unwrap()
    assert unwrapped == {"a": {"x": {"p": 1}, "y": {"q": 3}}, "foo": {"bar": 2}}
    _assert_plain(unwrapped)

    content = '[a.a]\nkey = "value"\n\n[a.b]\n\n[a.a.c]\n'
    doc2 = parse(content)
    table_unwrapped = doc2["a"].unwrap()
    assert table_unwrapped == {"a": {"key": "value", "c": {}}, "b": {}}
    _assert_plain(table_unwrapped)
    assert doc2.unwrap() == {"a": {"a": {"key": "value", "c": {}}, "b": {}}}
    assert doc2.as_string() == content


def test_conflicting_out_of_order_fragment_still_raises() -> None:
    doc = parse("[a]\nb = true\n[zz]\nq = 9\n[a.b]\narr = [1, 2]\n")
    with pytest.raises(KeyAlreadyPresent):
        doc.unwrap()


def test_multi_element_key_documents_unwrap() -> None:
    doc = tomlkit.document()
    doc.append(tomlkit.key(["a", "b"]), 1)
    doc.append(tomlkit.key(["a", "c"]), "x")
    doc.append("plain", 3)
    unwrapped = doc.unwrap()
    assert unwrapped == {"a": {"b": 1, "c": "x"}, "plain": 3}
    _assert_plain(unwrapped)
    assert parse(doc.as_string()).unwrap() == unwrapped
