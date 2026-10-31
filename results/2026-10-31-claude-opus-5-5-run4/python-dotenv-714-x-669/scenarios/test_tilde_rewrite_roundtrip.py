import io

import pytest

import dotenv
from dotenv.parser import parse_stream


def _home(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.chdir(tmp_path)
    return home


def test_tilde_path_crlf_values_and_set_key(tmp_path, monkeypatch):
    home = _home(tmp_path, monkeypatch)
    (home / ".env").write_bytes(b"bad: line\r\nc=d\r\ne=f\r\n")

    assert dotenv.dotenv_values("~/.env") == {"c": "d", "e": "f"}

    dotenv.set_key("~/.env", "c", "z")

    assert (home / ".env").read_text() == "bad: line\nc='z'\ne=f\n"
    assert dotenv.dotenv_values("~/.env") == {"c": "z", "e": "f"}


@pytest.mark.parametrize(
    "text",
    [
        "a: b\r\nc=d",
        "a: b\r\nc=d\r\ne: f",
        "a: b\r\n\r\nc=d\r\n",
        "x=1\r\na: b\r\n",
    ],
)
def test_crlf_stream_originals_roundtrip(text):
    bindings = list(parse_stream(io.StringIO(text)))

    assert "".join(b.original.string for b in bindings) == text
