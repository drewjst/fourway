from datetime import datetime, timedelta, timezone, tzinfo

import tomlkit
from tomlkit.items import item


class FoldTZ(tzinfo):
    def utcoffset(self, dt):
        return timedelta(hours=-5 if dt is not None and dt.fold else -4)

    def tzname(self, dt):
        return "FoldTZ"

    def dst(self, dt):
        return timedelta(0)


def test_fold_one_subtracts_to_zero() -> None:
    tz = FoldTZ()
    value = datetime(2018, 11, 4, 1, 30, tzinfo=tz, fold=1)
    other = datetime(2018, 11, 4, 6, 30, tzinfo=timezone.utc)
    assert value - other == timedelta(0)
    assert item(value) - other == timedelta(0)


def test_fold_preserved_for_datetime_stored_in_document() -> None:
    tz = FoldTZ()
    doc = tomlkit.document()
    doc["n"] = tomlkit.integer("42")
    doc["dt"] = item(datetime(2018, 11, 4, 1, 30, tzinfo=tz, fold=1))
    stored = doc["dt"]
    assert stored.fold == 1
    other = datetime(2018, 11, 4, 6, 30, tzinfo=timezone.utc)
    assert stored - other == timedelta(0)
    assert int(doc["n"]) == 42
