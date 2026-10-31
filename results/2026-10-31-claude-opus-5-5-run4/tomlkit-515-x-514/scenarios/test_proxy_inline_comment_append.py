from tomlkit import parse
from tomlkit.container import OutOfOrderTableProxy

CONTENT = (
    "[a.x]\np = 1\n[foo]\nbar = 2\n[a.y]\n"
    "tbl = {\n    p = { k = 1 },\n    q = { k = 2 }  # comment\n}\n"
)

EXPECTED_TBL = {"p": {"k": 1}, "q": {"k": 2}, "added": 3}


def _check_rendered(doc):
    rendered = doc.as_string()
    assert "# comment," not in rendered
    assert "q = { k = 2 },  # comment" in rendered
    reparsed = parse(rendered)
    assert reparsed.unwrap()["a"]["y"]["tbl"] == EXPECTED_TBL
    assert reparsed.unwrap()["a"]["x"] == {"p": 1}
    assert reparsed.unwrap()["foo"] == {"bar": 2}
    assert parse(rendered).as_string() == rendered


def test_append_into_commented_inline_table_via_out_of_order_proxy():
    doc = parse(CONTENT)
    proxy = doc["a"]
    assert isinstance(proxy, OutOfOrderTableProxy)
    assert "y" in proxy
    tbl = proxy["y"]["tbl"]
    assert "added" not in tbl
    tbl["added"] = 3
    assert "added" in tbl
    assert "added" in doc["a"]["y"]["tbl"]
    _check_rendered(doc)


def test_setdefault_into_commented_inline_table_via_out_of_order_proxy():
    doc = parse(CONTENT)
    proxy = doc["a"]
    assert isinstance(proxy, OutOfOrderTableProxy)
    tbl = proxy["y"]["tbl"]
    assert tbl.setdefault("added", 3) == 3
    # second call must not re-add
    assert tbl.setdefault("added", 99) == 3
    _check_rendered(doc)
