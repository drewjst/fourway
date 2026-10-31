import pytest

from tomlkit import parse
from tomlkit.exceptions import ParseError


CONTENT = (
    "[a.x]\n"
    'p = """\n'
    "l1\r\n"
    "l2\n"
    '"""\n'
    "[foo]\n"
    "bar = '''t\tq'''\n"
    "[a.y]\n"
    "q = '''multi\n"
    "line 'x' y'''\n"
)


def test_out_of_order_tables_with_multiline_values_round_trip() -> None:
    doc = parse(CONTENT)
    assert doc.as_string() == CONTENT

    a = doc["a"]
    assert "x" in a
    assert "y" in a
    assert "missing" not in a
    assert a["x"]["p"] == "l1\r\nl2\n"
    assert a["y"]["q"] == "multi\nline 'x' y"
    assert doc["foo"]["bar"] == "t\tq"

    assert doc.unwrap() == {
        "a": {"x": {"p": "l1\r\nl2\n"}, "y": {"q": "multi\nline 'x' y"}},
        "foo": {"bar": "t\tq"},
    }


def test_out_of_order_multiline_update_is_visible() -> None:
    doc = parse(CONTENT)
    doc["a"]["y"]["q"] = "new"
    rendered = doc.as_string()
    assert 'q = "new"' in rendered
    assert 'p = """\nl1\r\nl2\n"""' in rendered
    assert doc["a"]["y"]["q"] == "new"
    reparsed = parse(rendered)
    assert reparsed["a"]["y"]["q"] == "new"
    assert reparsed["a"]["x"]["p"] == "l1\r\nl2\n"


_PREFIX = "[a.x]\np = 1\n[foo]\nbar = 2\n[a.y]\n"


@pytest.mark.parametrize(
    "content",
    [
        _PREFIX + 'q = """ok\rbad"""\n',
        _PREFIX + 'q = """ok\x00bad"""\n',
        _PREFIX + 'q = """ok\x0cbad"""\n',
        _PREFIX + "q = '''ok\x7fbad'''\n",
        _PREFIX + "q = '''ok\rbad'''\n",
        _PREFIX + 'q = """never\nclosed\n',
        _PREFIX + "q = '''never\nclosed ''",
    ],
)
def test_invalid_multiline_in_out_of_order_fragment_rejected(content: str) -> None:
    with pytest.raises(ParseError):
        parse(content)
