import os
from unittest import mock

import dotenv
from dotenv.main import DotEnv


def test_bom_first_key_clean_through_cached_dict(tmp_path):
    path = tmp_path / ".env"
    path.write_text("\ufeffFIRST=1\nSECOND=2\n", encoding="utf-8")

    assert dotenv.dotenv_values(path) == {"FIRST": "1", "SECOND": "2"}

    obj = DotEnv(path, encoding="utf-8")
    with mock.patch.object(obj, "parse", wraps=obj.parse) as mock_parse:
        assert obj.get("FIRST") == "1"
        assert obj.get("SECOND") == "2"
        assert list(obj.dict().keys()) == ["FIRST", "SECOND"]
    assert mock_parse.call_count == 1


def test_bom_comment_only_file_loads_nothing(tmp_path):
    path = tmp_path / ".env"
    path.write_text("\ufeff# just a comment\n", encoding="utf-8")

    with mock.patch.dict(os.environ, {}, clear=True):
        result = dotenv.load_dotenv(path)
        assert result is False
        assert dict(os.environ) == {}

    assert dotenv.dotenv_values(path) == {}
