import pytest

import tomlkit

from tomlkit.source import Source


class _Runaway(Exception):
    pass


def _bounded_loads(text, monkeypatch, limit=20000):
    original = Source.inc
    calls = {"n": 0}

    def inc(self, exception=None):
        calls["n"] += 1
        if calls["n"] > limit:
            raise _Runaway("parser did not terminate")
        return original(self, exception=exception)

    monkeypatch.setattr(Source, "inc", inc)
    try:
        return tomlkit.loads(text)
    finally:
        monkeypatch.setattr(Source, "inc", original)


def test_crlf_multiline_basic_string_survives_sorted_dump(monkeypatch) -> None:
    text = 'zzz = """foo\r\nbar"""\naaa = 1\n'
    doc = _bounded_loads(text, monkeypatch)
    assert doc["zzz"] == "foo\r\nbar"
    out = tomlkit.dumps(doc, sort_keys=True)
    assert '"""foo\r\nbar"""' in out
    again = _bounded_loads(out, monkeypatch)
    assert again == {"zzz": "foo\r\nbar", "aaa": 1}


def test_crlf_multiline_literal_string_survives_sorted_dump(monkeypatch) -> None:
    text = "zzz = '''foo\r\nbar'''\naaa = 'x'\n"
    doc = _bounded_loads(text, monkeypatch)
    assert doc["zzz"] == "foo\r\nbar"
    out = tomlkit.dumps(doc, sort_keys=True)
    assert "'''foo\r\nbar'''" in out
    again = _bounded_loads(out, monkeypatch)
    assert again == {"zzz": "foo\r\nbar", "aaa": "x"}
