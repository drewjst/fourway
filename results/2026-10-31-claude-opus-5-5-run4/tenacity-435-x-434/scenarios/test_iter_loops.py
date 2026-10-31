import asyncio

import pytest

import tenacity
from tenacity import AsyncRetrying, RetryError, Retrying


def test_async_call_callback_order():
    events = []

    async def fake_sleep(s):
        events.append(("sleep", float(s)))

    def before(rs):
        events.append(("before", rs.attempt_number))

    def after(rs):
        events.append(("after", rs.attempt_number))

    def before_sleep(rs):
        events.append(("before_sleep", rs.attempt_number, rs.next_action.sleep))

    r = AsyncRetrying(
        sleep=fake_sleep,
        wait=tenacity.wait_fixed(0.5),
        stop=tenacity.stop_after_attempt(2),
        before=before,
        after=after,
        before_sleep=before_sleep,
    )

    async def fn():
        raise ValueError("x")

    with pytest.raises(RetryError):
        asyncio.run(r(fn))
    assert events == [
        ("before", 1),
        ("after", 1),
        ("before_sleep", 1, 0.5),
        ("sleep", 0.5),
        ("before", 2),
        ("after", 2),
    ]
    assert r.statistics["attempt_number"] == 2


def test_async_for_and_sync_for_loops():
    sleeps = []

    async def fake_sleep(s):
        sleeps.append(float(s))

    async def main():
        n = 0
        async for attempt in AsyncRetrying(
            sleep=fake_sleep,
            wait=tenacity.wait_fixed(1),
            retry=tenacity.retry_if_result(lambda x: x < 3),
        ):
            with attempt:
                n += 1
            attempt.retry_state.set_result(n)
        return n

    assert asyncio.run(main()) == 3
    assert sleeps == [1.0, 1.0]

    attempts = 0
    with pytest.raises(RetryError):
        for attempt in Retrying(sleep=lambda s: None, stop=tenacity.stop_after_attempt(3)):
            with attempt:
                attempts += 1
                raise Exception("fail")
    assert attempts == 3
