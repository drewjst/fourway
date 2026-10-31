import asyncio

import pytest

import tenacity
from tenacity import AsyncRetrying, RetryCallState, RetryError, Retrying, stop_after_attempt, wait_fixed


def _state(attempt):
    rs = RetryCallState(None, None, (), {})
    rs.attempt_number = attempt
    return rs


def test_sync_and_async_call_results_and_sleep_counts():
    sleeps = []
    calls = []

    def f(x, y=1):
        calls.append(x)
        if len(calls) < 3:
            raise IOError('x')
        return x + y

    r = Retrying(sleep=sleeps.append, wait=wait_fixed(1), stop=stop_after_attempt(5))
    assert r(f, 2, y=3) == 5
    assert sleeps == [1.0, 1.0]
    assert r.statistics['attempt_number'] == 3

    slept = []

    async def fake_sleep(s):
        slept.append(s)

    async def always_fail():
        raise ValueError('nope')

    ar = AsyncRetrying(sleep=fake_sleep, stop=stop_after_attempt(3))
    with pytest.raises(RetryError) as ei:
        asyncio.run(ar(always_fail))
    assert ei.value.last_attempt.attempt_number == 3
    assert slept == [0.0, 0.0]

    attempts = []

    async def iterate():
        async for attempt in AsyncRetrying(sleep=fake_sleep, stop=stop_after_attempt(4)):
            with attempt:
                attempts.append(1)
                if len(attempts) < 2:
                    raise ValueError('again')

    asyncio.run(iterate())
    assert len(attempts) == 2


def test_wait_defaults_unchanged():
    we = tenacity.wait_exponential()
    assert we(_state(1)) == 1
    assert we(_state(3)) == 4
    wi = tenacity.wait_incrementing()
    assert wi(_state(1)) == 0
    assert wi(_state(3)) == 200
    wc = tenacity.wait_exponential(multiplier=2, min=5, max=10)
    assert wc(_state(1)) == 5
    assert wc(_state(4)) == 10
