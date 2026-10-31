import tenacity
from tenacity import RetryError, Retrying

import pytest


def test_stop_before_idle_with_noop_before_sleep_stops_at_budget() -> None:
    sleeps: list[float] = []
    calls: list[int] = []
    before_sleep_calls: list[int] = []

    def always_fails() -> None:
        calls.append(1)
        raise ValueError("boom")

    def noop_before_sleep(rs: tenacity.RetryCallState) -> None:
        before_sleep_calls.append(rs.attempt_number)

    r = Retrying(
        stop=tenacity.stop_before_idle(3),
        wait=tenacity.wait_fixed(1),
        before_sleep=noop_before_sleep,
        sleep=sleeps.append,
    )
    with pytest.raises(RetryError):
        r(always_fails)
    assert sleeps == [1, 1, 1]
    assert len(calls) == 4
    assert before_sleep_calls == [1, 2, 3]
    assert r.statistics["idle_for"] == 3
    assert r.statistics["attempt_number"] == 4


def test_stop_before_idle_respects_budget_when_before_sleep_shortens_sleep() -> None:
    sleeps: list[float] = []

    def always_fails() -> None:
        raise ValueError("boom")

    def shorten(rs: tenacity.RetryCallState) -> None:
        rs.upcoming_sleep = 0.5

    r = Retrying(
        stop=tenacity.stop_before_idle(2) | tenacity.stop_after_attempt(20),
        wait=tenacity.wait_fixed(1),
        before_sleep=shorten,
        sleep=sleeps.append,
    )
    with pytest.raises(RetryError):
        r(always_fails)
    assert all(s == 0.5 for s in sleeps)
    assert len(sleeps) >= 2
    assert sum(sleeps) <= 2
