import importlib.util

import pytest

from tomlkit import parse
from tomlkit.exceptions import InvalidControlChar
from tomlkit.parser import Parser
from tomlkit.source import Source


def test_source_and_parser_use_plain_str_characters():
    text = 'a = { b . c = 1, "q".d = 2 }'
    src = Source(text)
    seen = []
    while not src.end():
        seen.append(src.current)
        src.inc()
    assert ''.join(seen) == text
    assert all(type(c) is str for c in seen)
    assert type(src.current) is str
    assert type(Source.EOF) is str

    p = Parser('a = {b.c = 1}')
    doc = p.parse()
    assert doc == {'a': {'b': {'c': 1}}}
    assert type(p._src.current) is str
    assert p.end()


def test_toml_char_module_removed_and_nul_not_eof():
    assert importlib.util.find_spec('tomlkit.toml_char') is None
    with pytest.raises(InvalidControlChar):
        parse('a = {b.c = "x\0y"}\n')
    doc = parse('a = {b.c = "xy"}')
    doc['a']['b']['d'] = 'z'
    assert parse(doc.as_string()) == {'a': {'b': {'c': 'xy', 'd': 'z'}}}
