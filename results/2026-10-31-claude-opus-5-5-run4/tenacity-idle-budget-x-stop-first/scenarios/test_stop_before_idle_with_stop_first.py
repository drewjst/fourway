import asyncio

import pytest

import tenacity
from tenacity import AsyncRetrying, RetryError, Retrying, stop_after_attempt


def always_fails() -> None:
    raise ValueError("boom")


def test_first_sleep_over_budget_is_not_taken() -> None:
    sleeps: list = []
    r = Retrying(
        stop=tenacity.stop_before_idle(1),
        wait=tenacity.wait_fixed(5),
        sleep=sleeps.append,
    )
    with pytest.raises(RetryError):
        r(always_fails)
    assert sleeps == []


def test_growing_waits_respect_idle_budget() -> None:
    def growing_wait(retry_state: tenacity.RetryCallState) -> float:
        return float(retry_state.attempt_number)

    sleeps: list = []
    r = Retrying(
        stop=tenacity.stop_before_idle(2.5),
        wait=growing_wait,
        sleep=sleeps.append,
    )
    with pytest.raises(RetryError):
        r(always_fails)
    assert sum(sleeps) <= 2.5
    assert sleeps == [1.0]


def test_combined_with_stop_after_attempt_respects_idle_budget() -> None:
    sleeps: list = []
    r = Retrying(
        stop=stop_after_attempt(10) | tenacity.stop_before_idle(1),
        wait=tenacity.wait_fixed(5),
        sleep=sleeps.append,
    )
    with pytest.raises(RetryError):
        r(always_fails)
    assert sleeps == []


def test_async_first_sleep_over_budget_is_not_taken() -> None:
    sleeps: list = []

    async def fake_sleep(seconds: float) -> None:
        sleeps.append(seconds)

    async def failing() -> None:
        raise ValueError("boom")

    async def run() -> None:
        r = AsyncRetrying(
            stop=tenacity.stop_before_idle(1),
            wait=tenacity.wait_fixed(5),
            sleep=fake_sleep,
        )
        with pytest.raises(RetryError):
            await r(failing)

    asyncio.run(run())
    assert sleeps == []
