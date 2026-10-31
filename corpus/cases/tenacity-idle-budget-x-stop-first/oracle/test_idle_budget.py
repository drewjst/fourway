import pytest

import tenacity
from tenacity import RetryError, Retrying


def always_fails():
    raise ValueError("boom")


def test_sleeping_stays_within_the_idle_budget():
    sleeps = []
    r = Retrying(
        stop=tenacity.stop_before_idle(2.5),
        wait=tenacity.wait_incrementing(start=1, increment=1),
        sleep=sleeps.append,
    )
    with pytest.raises(RetryError):
        r(always_fails)
    assert sleeps == [1]
