import pytest

from tomlkit import parse
from tomlkit.source import Source


@pytest.fixture
def error_counter(monkeypatch: pytest.MonkeyPatch) -> list:
    calls: list = []
    original = Source.parse_error

    def counting(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        calls.append(args)
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Source, "parse_error", counting)
    return calls


def test_empty_and_trailing_comma_arrays_build_no_error(error_counter: list) -> None:
    doc = parse("a = []\nb = [1, 2, ]\n")
    assert doc.value == {"a": [], "b": [1, 2]}
    assert error_counter == []


def test_out_of_order_tables_with_arrays_build_no_error(error_counter: list) -> None:
    content = "[a.b]\nx = [1, ]\n[a]\ny = []\n[a.c]\nz = [ ]\n"
    doc = parse(content)
    assert doc.as_string() == content
    assert error_counter == []
