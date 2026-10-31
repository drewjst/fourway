import tomlkit
from tomlkit import parse


def test_leading_newline_multiline_basic_string_with_comment_round_trips():
    s = tomlkit.string("\nfoo", multiline=True)
    s.comment("note")
    doc = tomlkit.document()
    doc["k"] = s
    rendered = doc.as_string()
    reparsed = parse(rendered)
    assert str(reparsed["k"]) == "\nfoo"
    assert reparsed.item("k").trivia.comment == "# note"
    assert parse(rendered).as_string() == rendered


def test_leading_newline_multiline_literal_string_with_comment_round_trips():
    s = tomlkit.string("\r\nbar", multiline=True, literal=True)
    s.comment("# already prefixed")
    doc = tomlkit.document()
    doc["k"] = s
    reparsed = parse(doc.as_string())
    assert str(reparsed["k"]) == "\r\nbar"
    assert reparsed.item("k").trivia.comment == "# already prefixed"
