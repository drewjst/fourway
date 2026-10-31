import tomlkit
from tomlkit import parse


def test_multiline_string_without_leading_newline_and_single_line_comment_round_trip():
    s = tomlkit.string("foo\nbar\n", multiline=True)
    assert s.as_string() == '"""foo\nbar\n"""'
    s.comment("note")
    doc = tomlkit.document()
    doc["k"] = s
    rendered = doc.as_string()
    assert rendered == 'k = """foo\nbar\n""" # note\n'
    reparsed = parse(rendered)
    assert str(reparsed["k"]) == "foo\nbar\n"
    assert reparsed.item("k").trivia.comment == "# note"
