import tomlkit


def test_crlf_multiline_basic_and_literal_preserved() -> None:
    basic = tomlkit.string("My\r\nString", multiline=True)
    assert basic.as_string() == '"""My\r\nString"""'
    literal = tomlkit.string("My\r\nString", multiline=True, literal=True)
    assert literal.as_string() == "'''My\r\nString'''"
    for s in (basic, literal):
        reparsed = tomlkit.parse("k = " + s.as_string() + "\n")
        assert reparsed["k"] == "My\r\nString"
