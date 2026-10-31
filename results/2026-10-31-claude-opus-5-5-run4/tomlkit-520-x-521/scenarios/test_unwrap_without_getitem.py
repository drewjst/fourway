import pytest

import tomlkit
from tomlkit.container import Container


def test_unwrap_does_not_go_through_getitem(monkeypatch: pytest.MonkeyPatch) -> None:
    doc = tomlkit.document()
    doc.append(tomlkit.key(["k"]), "v")
    doc.append(tomlkit.key(["d", "e"]), 2)
    doc.append("arr", [1, 2, 3])
    doc.append("t", {"x": 1, "sub": {"y": True}})

    def _boom(self, key):  # type: ignore[no-untyped-def]
        raise AssertionError("unwrap() must not resolve keys via __getitem__")

    monkeypatch.setattr(Container, "__getitem__", _boom)

    unwrapped = doc.unwrap()
    assert unwrapped == {
        "k": "v",
        "d": {"e": 2},
        "arr": [1, 2, 3],
        "t": {"x": 1, "sub": {"y": True}},
    }
    assert type(unwrapped["k"]) is str
    assert type(unwrapped["t"]["sub"]["y"]) is bool
