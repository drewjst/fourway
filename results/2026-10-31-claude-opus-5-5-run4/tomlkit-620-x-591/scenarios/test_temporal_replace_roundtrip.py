from datetime import date, datetime, time

from tomlkit import dumps, parse


def test_replaced_datetime_and_time_roundtrip_and_unwrap() -> None:
    content = "dt = 1979-05-27T07:32:00 # c\nt = 12:34:56\nd = 1979-05-27\nn = 1\n"
    doc = parse(content)
    assert doc["dt"].fold == 0
    assert doc["t"].fold == 0

    doc["dt"] = doc["dt"].replace(year=2000)
    doc["t"] = doc["t"].replace(hour=13)

    assert doc["dt"].fold == 0
    assert doc["t"].fold == 0
    expected = "dt = 2000-05-27T07:32:00 # c\nt = 13:34:56\nd = 1979-05-27\nn = 1\n"
    assert dumps(doc) == expected
    assert parse(dumps(doc)) == doc
    assert doc.unwrap() == {
        "dt": datetime(2000, 5, 27, 7, 32),
        "t": time(13, 34, 56),
        "d": date(1979, 5, 27),
        "n": 1,
    }


def test_assigning_plain_python_temporals_keeps_slots() -> None:
    doc = parse("a = 1\nb = 2\nc = 3\n")
    doc["a"] = datetime(2018, 7, 22, 12, 34, 56)
    doc["c"] = time(3, 8, 14)

    assert dumps(doc) == "a = 2018-07-22T12:34:56\nb = 2\nc = 03:08:14\n"
    assert doc.unwrap() == {
        "a": datetime(2018, 7, 22, 12, 34, 56),
        "b": 2,
        "c": time(3, 8, 14),
    }
