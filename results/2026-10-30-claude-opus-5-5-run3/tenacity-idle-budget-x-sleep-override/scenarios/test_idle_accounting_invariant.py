import tenacity
from tenacity import RetryError, Retrying

import pytest


def _always_fails() -> None:
    raise ValueError("boom")


def test_unchanged_sleep_counted_once_everywhere() -> None:
    sleeps: list[float] = []
    r = Retrying(
        stop=tenacity.stop_after_attempt(3),
        wait=tenacity.wait_fixed(1),
        before_sleep=lambda rs: None,
        sleep=sleeps.append,
        retry_error_callback=lambda rs: rs.idle_for,
    )
    final_idle = r(_always_fails)
    assert sleeps == [1, 1]
    assert final_idle == 2
    assert r.statistics["idle_for"] == 2
    assert r.statistics["attempt_number"] == 3


def test_before_sleep_runs_once_per_sleep_with_matching_next_action() -> None:
    sleeps: list[float] = []
    observed: list[tuple[int, float, float]] = []

    def watcher(rs: tenacity.RetryCallState) -> None:
        assert rs.next_action is not None
        observed.append((rs.attempt_number, rs.next_action.sleep, rs.idle_for))

    r = Retrying(
        stop=tenacity.stop_after_attempt(4),
        wait=tenacity.wait_incrementing(start=1, increment=1),
        before_sleep=watcher,
        sleep=sleeps.append,
    )
    with pytest.raises(RetryError):
        r(_always_fails)
    assert sleeps == [1, 2, 3]
    assert observed == [(1, 1.0, 1.0), (2, 2.0, 3.0), (3, 3.0, 6.0)]
    assert r.statistics["idle_for"] == 6
