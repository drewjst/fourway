import logging
import os
from unittest import mock

import dotenv


def _home(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    work = tmp_path / "work"
    work.mkdir()
    monkeypatch.chdir(work)
    return home


def test_find_dotenv_tilde_finds_crlf_file(tmp_path, monkeypatch):
    home = _home(tmp_path, monkeypatch)
    (home / ".env").write_bytes(b"bad: line\r\nDOTENV_MRG_A=1\r\n")

    result = dotenv.find_dotenv("~/.env", usecwd=True)

    assert result == os.path.join(str(home), ".env")


def test_load_found_tilde_file_with_crlf_invalid_line(tmp_path, monkeypatch, caplog):
    home = _home(tmp_path, monkeypatch)
    (home / ".env").write_bytes(
        b"bad: line\r\nDOTENV_MRG_C=d\r\nDOTENV_MRG_E=f\r\n"
    )
    caplog.set_level(logging.WARNING, logger="dotenv.main")

    with mock.patch.dict(os.environ, {}, clear=False):
        os.environ.pop("DOTENV_MRG_C", None)
        os.environ.pop("DOTENV_MRG_E", None)
        path = dotenv.find_dotenv("~/.env", usecwd=True)
        ok = dotenv.load_dotenv(path)
        c = os.environ.get("DOTENV_MRG_C")
        e = os.environ.get("DOTENV_MRG_E")

    assert ok is True
    assert (c, e) == ("d", "f")
    assert caplog.messages == [
        "python-dotenv could not parse statement starting at line 1"
    ]
