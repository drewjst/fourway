from datetime import timedelta

import pytest

import tomlkit
from tomlkit.items import Date
from tomlkit.items import DateTime


@pytest.mark.parametrize(
    "raw",
    ["1979-05-13T12:34:56", "1979-05-13T12:34:56Z", "1979-05-13 12:34:56-07:00"],
)
def test_date_factory_rejects_timestamps(raw: str) -> None:
    with pytest.raises(ValueError, match=r"date\(\) only accepts date strings"):
        tomlkit.date(raw)
    # the datetime factory still takes the same input
    assert isinstance(tomlkit.datetime(raw), DateTime)


def test_date_factory_accepts_dates_and_arithmetic_still_works() -> None:
    d = tomlkit.date("1979-05-13")
    assert isinstance(d, Date)
    assert not isinstance(d, DateTime)
    r = d + timedelta(days=1)
    assert isinstance(r, Date)
    assert r.as_string() == "1979-05-14"
    with pytest.raises(ValueError):
        tomlkit.date("1979-05-13T00:00:00")
