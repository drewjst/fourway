import asyncio

import pytest

import tenacity
from tenacity import retry, stop_after_attempt, wait_fixed


def test_async_sleep_awaited_per_retry_and_defaults_used():
    sleeps = []

    async def fake_sleep(seconds):
        sleeps.append(seconds)

    calls = []

    @retry(sleep=fake_sleep, stop=stop_after_attempt(5), wait=wait_fixed(0.5))
    async def flaky(a=1, *, b=2):
        calls.append((a, b))
        if len(calls) < 3:
            raise IOError("boom")
        return a + b

    assert asyncio.run(flaky()) == 3
    assert calls == [(1, 2), (1, 2), (1, 2)]
    assert sleeps == [0.5, 0.5]


def test_async_sleep_exhaustion_raises_retry_error_once():
    sleeps = []

    async def fake_sleep(seconds):
        sleeps.append(seconds)

    calls = []

    @retry(sleep=fake_sleep, stop=stop_after_attempt(3), wait=wait_fixed(1))
    async def always_fail(*, tag="t"):
        calls.append(tag)
        raise ValueError(tag)

    with pytest.raises(tenacity.RetryError):
        asyncio.run(always_fail())
    assert calls == ["t", "t", "t"]
    assert sleeps == [1.0, 1.0]


def test_sync_sleep_and_defaults():
    sleeps = []
    calls = []

    @retry(sleep=sleeps.append, stop=stop_after_attempt(4), wait=wait_fixed(2))
    def flaky(x, y=5, *, z=7):
        calls.append((x, y, z))
        if len(calls) < 2:
            raise IOError("again")
        return x + y + z

    assert flaky(1) == 13
    assert calls == [(1, 5, 7), (1, 5, 7)]
    assert sleeps == [2.0]
