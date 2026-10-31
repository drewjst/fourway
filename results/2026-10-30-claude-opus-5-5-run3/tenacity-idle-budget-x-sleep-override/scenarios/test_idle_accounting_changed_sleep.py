import tenacity
from tenacity import Retrying


def _always_fails() -> None:
    raise ValueError("boom")


def _honor_retry_after(rs: tenacity.RetryCallState) -> None:
    rs.upcoming_sleep = 7.0


def test_stop_strategy_sees_actual_idle_time() -> None:
    sleeps: list[float] = []
    seen_idle: list[float] = []

    def recording_stop(rs: tenacity.RetryCallState) -> bool:
        seen_idle.append(rs.idle_for)
        return rs.attempt_number >= 3

    r = Retrying(
        stop=recording_stop,
        wait=tenacity.wait_fixed(1),
        before_sleep=_honor_retry_after,
        sleep=sleeps.append,
        retry_error_callback=lambda rs: None,
    )
    r(_always_fails)
    assert sleeps == [7.0, 7.0]
    assert seen_idle == [0.0, 7.0, 14.0]


def test_final_idle_for_matches_actual_sleeps() -> None:
    sleeps: list[float] = []

    r = Retrying(
        stop=tenacity.stop_after_attempt(3),
        wait=tenacity.wait_fixed(1),
        before_sleep=_honor_retry_after,
        sleep=sleeps.append,
        retry_error_callback=lambda rs: rs.idle_for,
    )
    final_idle = r(_always_fails)
    assert sleeps == [7.0, 7.0]
    assert final_idle == sum(sleeps) == 14.0
    assert r.statistics["idle_for"] == 14.0
