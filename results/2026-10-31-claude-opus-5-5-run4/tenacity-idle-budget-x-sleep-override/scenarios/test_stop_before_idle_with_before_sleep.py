import asyncio

import pytest

import tenacity
from tenacity import AsyncRetrying, RetryError, Retrying


def _failing(calls):
    def f():
        calls.append(1)
        raise ValueError("boom")

    return f


def test_stop_before_idle_counts_each_sleep_once_with_before_sleep():
    sleeps = []
    seen = []
    calls = []

    def bs(rs):
        seen.append(rs.next_action.sleep)

    r = Retrying(
        stop=tenacity.stop_before_idle(2.5),
        wait=tenacity.wait_fixed(1),
        before_sleep=bs,
        sleep=sleeps.append,
    )
    with pytest.raises(RetryError):
        r(_failing(calls))
    assert sleeps == [1.0, 1.0]
    assert seen == [1.0, 1.0]
    assert len(calls) == 3
    assert r.statistics["idle_for"] == 2


class _FakeTime:
    def __init__(self):
        self.now = 0.0

    def monotonic(self):
        self.now += 100.0
        return self.now


def test_slow_attempts_and_unchanged_override_do_not_eat_idle_budget(monkeypatch):
    monkeypatch.setattr(tenacity, "time", _FakeTime())
    sleeps = []
    calls = []

    def keep_same(rs):
        rs.upcoming_sleep = rs.upcoming_sleep

    r = Retrying(
        stop=tenacity.stop_before_idle(2.5),
        wait=tenacity.wait_fixed(1),
        before_sleep=keep_same,
        sleep=sleeps.append,
    )
    with pytest.raises(RetryError):
        r(_failing(calls))
    assert sleeps == [1.0, 1.0]
    assert len(calls) == 3
    assert r.statistics["idle_for"] == 2
    assert r.statistics["delay_since_first_attempt"] > 2.5


def test_async_stop_before_idle_with_before_sleep():
    sleeps = []
    calls = []

    async def rec(s):
        sleeps.append(s)

    async def f():
        calls.append(1)
        raise ValueError("boom")

    r = AsyncRetrying(
        stop=tenacity.stop_before_idle(2.5),
        wait=tenacity.wait_fixed(1),
        before_sleep=lambda rs: None,
        sleep=rec,
    )

    async def main():
        with pytest.raises(RetryError):
            await r(f)

    asyncio.run(main())
    assert sleeps == [1.0, 1.0]
    assert len(calls) == 3
    assert r.statistics["idle_for"] == 2
