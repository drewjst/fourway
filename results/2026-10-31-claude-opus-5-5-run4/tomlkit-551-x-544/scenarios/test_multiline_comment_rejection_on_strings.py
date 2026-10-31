import pytest

import tomlkit
from tomlkit import api


def test_comment_with_line_break_rejected_on_leading_newline_multiline_string():
    s = tomlkit.string("\nfoo", multiline=True)
    before = s.as_string()
    with pytest.raises(ValueError):
        s.comment("first\nsecond")
    assert s.trivia.comment == ""
    assert s.as_string() == before
    doc = tomlkit.document()
    doc["k"] = s
    assert doc.as_string() == f"k = {before}\n"


def test_add_line_with_multiline_string_and_line_break_comment_rejected():
    t = api.array()
    with pytest.raises(ValueError):
        t.add_line(tomlkit.string("\nfoo", multiline=True), comment="a\r\nb")
    assert t.as_string() == "[]"
    assert len(t) == 0
