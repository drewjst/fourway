from datetime import datetime, time

from tomlkit import dumps, parse


def test_unwrap_order_after_replacing_time_with_fold() -> None:
    doc = parse("a = 1\nt = 12:00:00\nc = 3\n")
    doc["t"] = time(1, 30, fold=1)

    unwrapped = doc.unwrap()
    assert list(unwrapped) == ["a", "t", "c"]
    assert list(doc.keys()) == ["a", "t", "c"]
    assert unwrapped["t"] == time(1, 30)
    assert dumps(doc) == "a = 1\nt = 01:30:00\nc = 3\n"


def test_unwrap_order_after_replacing_datetime_via_replace() -> None:
    doc = parse("d = 1979-05-27T07:32:00\nx = 2\ny = 3\n")
    doc["d"] = doc["d"].replace(year=2000)
    doc["x"] = datetime(2021, 11, 7, 1, 30, fold=1)

    unwrapped = doc.unwrap()
    assert list(unwrapped) == ["d", "x", "y"]
    assert unwrapped["d"] == datetime(2000, 5, 27, 7, 32)
    assert unwrapped["x"] == datetime(2021, 11, 7, 1, 30)
    assert dumps(doc) == (
        "d = 2000-05-27T07:32:00\nx = 2021-11-07T01:30:00\ny = 3\n"
    )
