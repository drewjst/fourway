import datetime

from tomlkit import api
from tomlkit import document
from tomlkit import item
from tomlkit import parse


def test_naive_time_rendering_unchanged():
    assert item(datetime.time(12, 34, 56)).as_string() == "12:34:56"
    assert item(datetime.time(12, 34, 56, 123456)).as_string() == "12:34:56.123456"
    t = item(datetime.time(12, 34, 56)).replace(hour=13)
    assert t.as_string() == "13:34:56"


def test_string_plus_string_and_plain_text_preserved():
    i = api.value('"foo\\"bar"')
    i += " baz"
    assert i == 'foo"bar baz'
    assert i.as_string() == '"foo\\"bar baz"'
    j = item("a")
    j += api.value('"x\\ty"')
    assert j == "ax\ty"
    assert j.as_string() == '"ax\\ty"'


def test_document_with_naive_time_and_extended_string_round_trips():
    doc = document()
    doc["s"] = "foo"
    doc["s"] += " bar"
    doc["t"] = datetime.time(7, 32)
    rendered = doc.as_string()
    assert rendered == 's = "foo bar"\nt = 07:32:00\n'
    reparsed = parse(rendered)
    assert reparsed["s"] == "foo bar"
    assert reparsed["t"] == datetime.time(7, 32)
