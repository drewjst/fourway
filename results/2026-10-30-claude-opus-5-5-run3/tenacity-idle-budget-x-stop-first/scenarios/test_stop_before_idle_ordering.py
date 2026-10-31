import asyncio

import pytest

import tenacity
from tenacity import RetryError, Retrying


def always_fails() -> None:
    raise ValueError("boom")


def test_first_sleep_over_budget_is_never_taken() -> None:
    sleeps: list[float] = []
    r = Retrying(
        stop=tenacity.stop_before_idle(5),
        wait=tenacity.wait_fixed(10),
        sleep=sleeps.append,
    )
    with pytest.raises(RetryError) as exc_info:
        r(always_fails)
    assert sleeps == []
    assert exc_info.value.last_attempt.attempt_number == 1


def test_growing_wait_checked_against_its_own_upcoming_sleep() -> None:
    # wait: 1s after attempt 1, 4s after attempt 2. Budget 4s total.
    sleeps: list[float] = []
    r = Retrying(
        stop=tenacity.stop_before_idle(4),
        wait=tenacity.wait_incrementing(start=1, increment=3),
        sleep=sleeps.append,
    )
    with pytest.raises(RetryError):
        r(always_fails)
    assert sleeps == [1.0]
    assert sum(sleeps) <= 4


def test_combined_with_attempt_limit_respects_idle_budget() -> None:
    sleeps: list[float] = []
    r = Retrying(
        stop=tenacity.stop_after_attempt(10) | tenacity.stop_before_idle(4),
        wait=tenacity.wait_incrementing(start=1, increment=3),
        sleep=sleeps.append,
    )
    with pytest.raises(RetryError):
        r(always_fails)
    assert sum(sleeps) <= 4
    assert sleeps == [1.0]


def test_async_first_sleep_over_budget_is_never_taken() -> None:
    sleeps: list[float] = []

    async def fake_sleep(seconds: float) -> None:
        sleeps.append(seconds)

    async def fails() -> None:
        raise ValueError("boom")

    r = tenacity.AsyncRetrying(
        stop=tenacity.stop_before_idle(5),
        wait=tenacity.wait_fixed(10),
        sleep=fake_sleep,
    )

    async def main() -> None:
        with pytest.raises(RetryError):
            await r(fails)

    asyncio.run(main())
    assert sleeps == []
