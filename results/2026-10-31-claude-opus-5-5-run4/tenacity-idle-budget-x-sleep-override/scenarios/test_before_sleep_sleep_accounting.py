import asyncio

import pytest

import tenacity
from tenacity import AsyncRetrying, RetryError, Retrying, stop_after_attempt


def _fails():
    raise ValueError("boom")


def test_idle_budget_stop_sees_overridden_sleep():
    sleeps = []

    def honor_retry_after(rs):
        rs.upcoming_sleep = 7

    def idle_budget(rs):
        return rs.idle_for + rs.upcoming_sleep > 10

    r = Retrying(
        stop=tenacity.stop_any(stop_after_attempt(20), idle_budget),
        wait=tenacity.wait_fixed(1),
        before_sleep=honor_retry_after,
        sleep=sleeps.append,
    )
    with pytest.raises(RetryError):
        r(_fails)
    assert sleeps == [7, 7]
    assert r.statistics["idle_for"] == 14


def test_idle_for_visible_to_next_attempt_matches_actual_sleep():
    sleeps = []
    idle_seen = []

    def honor_retry_after(rs):
        rs.upcoming_sleep = 7

    r = Retrying(
        stop=stop_after_attempt(3),
        wait=tenacity.wait_fixed(1),
        before=lambda rs: idle_seen.append(rs.idle_for),
        before_sleep=honor_retry_after,
        sleep=sleeps.append,
    )
    with pytest.raises(RetryError):
        r(_fails)
    assert sleeps == [7, 7]
    assert idle_seen == [0, 7, 14]


def test_async_before_sleep_override_counted():
    sleeps = []

    async def rec(s):
        sleeps.append(s)

    async def bs(rs):
        rs.upcoming_sleep = 3

    async def f():
        raise ValueError("boom")

    r = AsyncRetrying(
        stop=stop_after_attempt(3),
        wait=tenacity.wait_fixed(1),
        before_sleep=bs,
        sleep=rec,
    )

    async def main():
        with pytest.raises(RetryError):
            await r(f)

    asyncio.run(main())
    assert sleeps == [3, 3]
    assert r.statistics["idle_for"] == 6
