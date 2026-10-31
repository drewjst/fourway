from tomlkit import parse


def test_add_to_quoted_dotted_key_at_eof_and_crlf():
    doc = parse('a = {"b".c = 1}')
    doc['a']['b']['d'] = 2
    rendered = doc.as_string()
    assert rendered == 'a = {"b".c = 1, "b".d = 2}'
    assert parse(rendered) == {'a': {'b': {'c': 1, 'd': 2}}}
    assert parse(rendered).as_string() == rendered

    doc = parse('[t]\r\nx = {b.c = 1}\r\n')
    doc['t']['x']['b']['d'] = 2
    rendered = doc.as_string()
    assert rendered == '[t]\r\nx = {b.c = 1, b.d = 2}\r\n'
    assert parse(rendered) == {'t': {'x': {'b': {'c': 1, 'd': 2}}}}


def test_add_to_dotted_key_with_tabs_around_separators():
    doc = parse('a = {b\t.\tc\t=\t1}\n')
    doc['a']['b']['d'] = 2
    rendered = doc.as_string()
    reparsed = parse(rendered)
    assert reparsed == {'a': {'b': {'c': 1, 'd': 2}}}
    assert reparsed.as_string() == rendered
    assert rendered.endswith('}\n')


def test_add_to_nested_spaced_dotted_key():
    doc = parse('a = { b . c . e = 1 }\n')
    doc['a']['b']['c']['g'] = 2
    rendered = doc.as_string()
    reparsed = parse(rendered)
    assert reparsed == {'a': {'b': {'c': {'e': 1, 'g': 2}}}}
    assert reparsed.as_string() == rendered
