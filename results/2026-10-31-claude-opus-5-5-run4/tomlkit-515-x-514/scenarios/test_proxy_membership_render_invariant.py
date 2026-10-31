import pytest

from tomlkit import parse
from tomlkit.container import OutOfOrderTableProxy

CONTENT = (
    "[a.x]\np = 1\nt = {m = 1, n = 2}\n[foo]\nbar = 2\n[a.y]\nq = 3\n"
)


def test_membership_and_append_through_proxy_round_trip():
    doc = parse(CONTENT)
    proxy = doc["a"]
    assert isinstance(proxy, OutOfOrderTableProxy)

    before = doc.as_string()
    assert "x" in proxy
    assert "y" in proxy
    assert "t" not in proxy
    assert "missing" not in proxy
    with pytest.raises(TypeError):
        _ = 123 in proxy
    assert doc.as_string() == before

    t = proxy["x"]["t"]
    t["o"] = 3
    assert "o" in t

    after = doc.as_string()
    assert "x" in doc["a"]
    assert "missing" not in doc["a"]
    assert doc.as_string() == after

    reparsed = parse(after)
    assert reparsed.unwrap() == {
        "a": {"x": {"p": 1, "t": {"m": 1, "n": 2, "o": 3}}, "y": {"q": 3}},
        "foo": {"bar": 2},
    }
    assert parse(after).as_string() == after
