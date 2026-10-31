import pytest

import tomlkit
from tomlkit.items import Null


def _expected_map(array):
    return dict(
        enumerate(
            i
            for i, g in enumerate(array._value)
            if g.value is not None and not isinstance(g.value, Null)
        )
    )


def _boom() -> None:
    raise AssertionError("tail append must not rebuild indexes")


def test_fresh_array_tail_appends_skip_reindex(monkeypatch: pytest.MonkeyPatch) -> None:
    array = tomlkit.array()
    monkeypatch.setattr(array, "_reindex", _boom)
    array.extend(range(50))
    assert array == list(range(50))
    assert array._index_map == _expected_map(array)


def test_parsed_multiline_tail_appends_skip_reindex(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    doc = tomlkit.parse("x = [\n  1,\n  2,\n]\n")
    array = doc["x"]
    monkeypatch.setattr(array, "_reindex", _boom)
    array.append(3)
    array.append("four")
    assert array == [1, 2, 3, "four"]
    assert array._index_map == _expected_map(array)
    assert tomlkit.parse(doc.as_string())["x"] == [1, 2, 3, "four"]
