from datetime import datetime, time, timedelta, tzinfo

import tomlkit


class FoldTZ(tzinfo):
    def utcoffset(self, dt):
        return timedelta(hours=-5 if dt is not None and dt.fold else -4)

    def tzname(self, dt):
        return "FoldTZ"

    def dst(self, dt):
        return timedelta(0)


def test_document_unwrap_keeps_datetime_fold() -> None:
    tz = FoldTZ()
    value = datetime(2018, 11, 4, 1, 30, tzinfo=tz, fold=1)
    doc = tomlkit.document()
    doc["dt"] = tomlkit.item(value)
    out = doc.unwrap()["dt"]
    assert type(out) is datetime
    assert out.fold == 1
    assert out.timestamp() == value.timestamp()


def test_document_unwrap_keeps_time_fold() -> None:
    doc = tomlkit.document()
    doc["t"] = tomlkit.item(time(1, 30, fold=1))
    out = doc.unwrap()["t"]
    assert type(out) is time
    assert out.fold == 1
