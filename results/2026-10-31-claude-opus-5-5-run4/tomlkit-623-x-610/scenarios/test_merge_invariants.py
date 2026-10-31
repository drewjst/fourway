from datetime import datetime, timedelta, timezone, tzinfo

import pytest

import tomlkit
from tomlkit.items import DateTime, item


class FoldTZ(tzinfo):
    def utcoffset(self, dt):
        return timedelta(hours=-5 if dt is not None and dt.fold else -4)

    def tzname(self, dt):
        return "FoldTZ"

    def dst(self, dt):
        return timedelta(0)


def test_timedelta_subtraction_matches_stdlib() -> None:
    tz = FoldTZ()
    value = datetime(2018, 11, 4, 1, 30, tzinfo=tz, fold=1)
    expected = value - timedelta(hours=1)
    result = item(value) - timedelta(hours=1)
    assert isinstance(result, DateTime)
    assert result == expected
    assert result.fold == 0
    assert result.as_string() == expected.isoformat()


def test_datetime_difference_with_fold_zero() -> None:
    tz = FoldTZ()
    value = datetime(2018, 11, 4, 1, 30, tzinfo=tz)
    other = datetime(2018, 11, 4, 5, 30, tzinfo=timezone.utc)
    assert item(value) - other == value - other == timedelta(0)


def test_integer_plain_forms_unchanged_and_garbage_rejected() -> None:
    assert tomlkit.integer(1000).as_string() == "1000"
    assert tomlkit.integer("42").as_string() == "42"
    assert int(tomlkit.integer("42")) == 42
    doc = tomlkit.document()
    doc["n"] = tomlkit.integer("7")
    doc["n"] += 1
    assert tomlkit.dumps(doc) == "n = 8\n"
    with pytest.raises(ValueError):
        tomlkit.integer("abc")
