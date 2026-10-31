from datetime import datetime, time

from tomlkit import parse


def test_time_fold_kept_when_replacing_value_in_document() -> None:
    doc = parse("a = 1\nt = 12:00:00\nc = 3\n")
    doc["t"] = time(1, 30, fold=1)

    assert doc["t"].fold == 1
    assert doc["t"] == time(1, 30)
    assert doc.as_string() == "a = 1\nt = 01:30:00\nc = 3\n"

    replaced = doc["t"].replace(minute=45)
    assert replaced.fold == 1
    doc["t"] = replaced
    assert doc["t"].fold == 1
    assert doc.as_string() == "a = 1\nt = 01:45:00\nc = 3\n"


def test_datetime_fold_kept_when_replacing_value_in_document() -> None:
    doc = parse("a = 1\nd = 1979-05-27T07:32:00\nc = 3\n")
    doc["d"] = doc["d"].replace(fold=1)

    assert doc["d"].fold == 1
    assert doc["d"] == datetime(1979, 5, 27, 7, 32)
    assert doc.as_string() == "a = 1\nd = 1979-05-27T07:32:00\nc = 3\n"

    doc["d"] = datetime(2021, 11, 7, 1, 30, fold=1)
    assert doc["d"].fold == 1
    assert doc.as_string() == "a = 1\nd = 2021-11-07T01:30:00\nc = 3\n"
