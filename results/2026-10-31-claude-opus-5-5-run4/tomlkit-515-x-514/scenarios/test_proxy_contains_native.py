import tomlkit.container as container_mod

from tomlkit import parse
from tomlkit.container import OutOfOrderTableProxy
from tomlkit.exceptions import NonExistentKey

CONTENT = (
    "[a.x]\np = 1\n[foo]\nbar = 2\n[a.y]\n"
    "tbl = {\n    p = { k = 1 },\n    q = { k = 2 }  # comment\n}\n"
)


def _prepared_doc():
    doc = parse(CONTENT)
    doc["a"]["y"]["tbl"]["added"] = 3
    return doc


def test_proxy_membership_does_not_resolve_values(monkeypatch):
    doc = _prepared_doc()
    proxy = doc["a"]
    assert isinstance(proxy, OutOfOrderTableProxy)

    calls = []
    original = OutOfOrderTableProxy.__getitem__

    def counting(self, key):
        calls.append(key)
        return original(self, key)

    monkeypatch.setattr(OutOfOrderTableProxy, "__getitem__", counting)

    assert "x" in proxy
    assert "y" in proxy
    assert "missing" not in proxy
    assert calls == []
    # rendering is untouched by membership
    assert "q = { k = 2 },  # comment" in doc.as_string()


def test_proxy_absent_membership_builds_no_exception(monkeypatch):
    doc = _prepared_doc()
    proxy = doc["a"]
    assert isinstance(proxy, OutOfOrderTableProxy)

    built = []

    class CountingNonExistentKey(NonExistentKey):
        def __init__(self, key):
            built.append(key)
            super().__init__(key)

    monkeypatch.setattr(container_mod, "NonExistentKey", CountingNonExistentKey)

    assert "missing" not in proxy
    assert "added" not in proxy
    assert built == []
