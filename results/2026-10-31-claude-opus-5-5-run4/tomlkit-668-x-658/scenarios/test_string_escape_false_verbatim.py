import tomlkit


def test_multiline_basic_escape_false_is_verbatim() -> None:
    s = tomlkit.string("\nfoo", multiline=True, escape=False)
    assert str(s) == "\nfoo"
    assert s.as_string() == '"""\nfoo"""'


def test_multiline_literal_escape_false_is_verbatim() -> None:
    s = tomlkit.string("\nbar", multiline=True, literal=True, escape=False)
    assert str(s) == "\nbar"
    assert s.as_string() == "'''\nbar'''"
