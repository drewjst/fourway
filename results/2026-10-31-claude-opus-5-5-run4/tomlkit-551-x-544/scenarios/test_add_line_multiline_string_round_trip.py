import tomlkit
from tomlkit import api
from tomlkit import parse


def test_add_line_leading_newline_multiline_string_with_comment_round_trips():
    t = api.array()
    t.add_line(tomlkit.string("\nfoo", multiline=True), comment="note")
    t.add_line(indent="")
    rendered = f"a = {t.as_string()}\n"
    reparsed = parse(rendered)
    assert [str(v) for v in reparsed["a"]] == ["\nfoo"]
    assert "# note" in rendered
    assert parse(rendered).as_string() == rendered
