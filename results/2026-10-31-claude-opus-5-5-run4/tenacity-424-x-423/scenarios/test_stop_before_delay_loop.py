import asyncio
import types

import pytest

import tenacity


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def monotonic(self):
        return self.now


@pytest.fixture
def clock(monkeypatch):
    c = FakeClock()
    monkeypatch.setattr(tenacity, "time", types.SimpleNamespace(monotonic=c.monotonic))
    return c


def test_stop_before_delay_never_exceeds_deadline_sync(clock):
    from tenacity import stop_before_delay

    sleeps = []
    calls = []

    def fake_sleep(s):
        sleeps.append(s)
        clock.now += s

    def fn():
        calls.append(clock.now)
        raise ValueError("boom")

    r = tenacity.Retrying(
        sleep=fake_sleep,
        stop=stop_before_delay(5),
        wait=tenacity.wait_exponential(),
    )
    with pytest.raises(tenacity.RetryError) as ei:
        r(fn)
    assert calls == [0.0, 1.0, 3.0]
    assert sleeps == [1.0, 2.0]
    assert ei.value.last_attempt.attempt_number == 3
    assert clock.now < 5


def test_custom_stop_sees_upcoming_sleep(clock):
    seen = []

    def my_stop(retry_state):
        seen.append(retry_state.upcoming_sleep)
        return retry_state.attempt_number >= 3

    sleeps = []

    def fake_sleep(s):
        sleeps.append(s)
        clock.now += s

    r = tenacity.Retrying(
        sleep=fake_sleep,
        stop=my_stop,
        wait=tenacity.wait_incrementing(start=1, increment=1),
    )

    def fn():
        raise ValueError("x")

    with pytest.raises(tenacity.RetryError):
        r(fn)
    assert seen == [1.0, 2.0, 3.0]
    assert sleeps == [1.0, 2.0]


def test_stop_before_delay_async(clock):
    from tenacity import stop_before_delay

    sleeps = []
    calls = []

    async def fake_sleep(s):
        sleeps.append(s)
        clock.now += s

    async def fn():
        calls.append(clock.now)
        raise ValueError("boom")

    r = tenacity.AsyncRetrying(
        sleep=fake_sleep,
        stop=stop_before_delay(5),
        wait=tenacity.wait_exponential(),
        reraise=True,
    )

    async def main():
        return await r(fn)

    with pytest.raises(ValueError):
        asyncio.run(main())
    assert calls == [0.0, 1.0, 3.0]
    assert sleeps == [1.0, 2.0]
