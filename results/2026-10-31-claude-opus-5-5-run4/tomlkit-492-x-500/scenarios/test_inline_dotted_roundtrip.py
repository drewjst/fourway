import pytest

from tomlkit import parse


CASES = [
    'a = {b.c = 1}\n',
    'a = {b.c = 1}',
    'a = { b . c = 1 }\n',
    'a = {\tb\t.\tc\t=\t1}\n',
    'a = {"b c".\'d\' = 1, x.y.z = 2}\n',
    'a = {b.c = 1, b.d = 2}',
    '[t]\r\nx = {b.c = 1, y = 3}\r\n',
    'a = {\n  b.c = 1,\n}\n',
]


@pytest.mark.parametrize('content', CASES)
def test_unmodified_inline_dotted_tables_round_trip(content):
    doc = parse(content)
    assert doc.as_string() == content
    again = parse(doc.as_string())
    assert again == doc
    assert again.as_string() == content


def test_replacing_sibling_key_keeps_dotted_pair():
    doc = parse('a = {b.c = 1, x = 2}\n')
    doc['a']['x'] = 3
    rendered = doc.as_string()
    assert rendered == 'a = {b.c = 1, x = 3}\n'
    assert parse(rendered) == {'a': {'b': {'c': 1}, 'x': 3}}
