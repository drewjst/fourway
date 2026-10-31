import pytest

from tomlkit import parse
from tomlkit.exceptions import UnexpectedCharError
from tomlkit.toml_file import TOMLFile


def test_crlf_document_with_datetime_reports_true_position() -> None:
    content = "a = 1979-05-27T07:32:00\r\nb = 2\r\nc = @\r\n"
    with pytest.raises(UnexpectedCharError) as e:
        parse(content)
    assert e.value.line == 3
    assert e.value.col == 4


def test_mixed_endings_file_read_reports_true_position(tmp_path) -> None:
    path = tmp_path / "mixed.toml"
    with open(path, "wb") as fh:
        fh.write(b"a = 1\r\nb = 2\nc = @\r\n")
    with pytest.raises(UnexpectedCharError) as e:
        TOMLFile(path).read()
    assert e.value.line == 3
    assert e.value.col == 4
