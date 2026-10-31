import datetime

from tomlkit import document
from tomlkit import item
from tomlkit import parse


TZ = datetime.timezone(datetime.timedelta(hours=2))


def test_tz_aware_time_in_document_round_trips():
    doc = document()
    doc["s"] = "foo"
    doc["s"] += " bar"
    doc["t"] = datetime.time(7, 32, tzinfo=TZ)
    doc["u"] = datetime.time(7, 32, 0, 500000, tzinfo=TZ)
    rendered = doc.as_string()
    reparsed = parse(rendered)
    assert reparsed["s"] == "foo bar"
    assert reparsed["t"] == datetime.time(7, 32)
    assert reparsed["u"] == datetime.time(7, 32, 0, 500000)


def test_tz_aware_time_replace_renders_local():
    t = item(datetime.time(7, 32, tzinfo=TZ))
    assert t.as_string() == "07:32:00"
    r = t.replace(hour=13)
    assert r.as_string() == "13:32:00"
    assert parse(f"t = {r.as_string()}")["t"] == datetime.time(13, 32)
