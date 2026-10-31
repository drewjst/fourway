import os
from unittest import mock

import dotenv
from dotenv.main import DotEnv


def test_nonempty_dict_cached_same_object(tmp_path):
    path = tmp_path / ".env"
    path.write_text("a=b\nc=${a}\n", encoding="utf-8")
    obj = DotEnv(path, encoding="utf-8")

    with mock.patch.object(obj, "parse", wraps=obj.parse) as mock_parse:
        first = obj.dict()
        second = obj.dict()

    assert first is second
    assert first == {"a": "b", "c": "b"}
    assert mock_parse.call_count == 1


def test_empty_file_load_returns_false_and_env_untouched(tmp_path):
    path = tmp_path / ".env"
    path.write_text("", encoding="utf-8")

    with mock.patch.dict(os.environ, {"KEEP": "1"}, clear=True):
        assert dotenv.load_dotenv(path) is False
        assert dotenv.load_dotenv(path, override=True) is False
        assert dict(os.environ) == {"KEEP": "1"}

    assert dotenv.dotenv_values(path) == {}
