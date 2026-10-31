from unittest import mock

from dotenv.main import DotEnv


def test_bom_only_file_is_empty_and_parsed_once(tmp_path):
    path = tmp_path / ".env"
    path.write_text("\ufeff", encoding="utf-8")
    obj = DotEnv(path, encoding="utf-8")

    with mock.patch.object(obj, "parse", wraps=obj.parse) as mock_parse:
        first = obj.dict()
        second = obj.dict()

    assert first == {}
    assert second == {}
    assert mock_parse.call_count == 1


def test_empty_file_parsed_once(tmp_path):
    path = tmp_path / ".env"
    path.write_text("", encoding="utf-8")
    obj = DotEnv(path, encoding="utf-8")

    with mock.patch.object(obj, "parse", wraps=obj.parse) as mock_parse:
        assert obj.dict() == {}
        assert obj.dict() == {}
        assert obj.get("missing") is None

    assert mock_parse.call_count == 1
