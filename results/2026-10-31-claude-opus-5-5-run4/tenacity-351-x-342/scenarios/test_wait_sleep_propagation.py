import pytest

import tenacity


@pytest.mark.parametrize(
    "wait,expected",
    [
        (tenacity.wait_fixed(0.5), [0.5, 0.5, 0.5, 0.5]),
        (tenacity.wait_exponential(multiplier=1, min=1, max=4), [1.0, 2.0, 4.0, 4.0]),
    ],
)
def test_numeric_waits_reach_sleep_and_callbacks(wait, expected):
    sleeps = []
    announced = []

    def before_sleep(rs):
        announced.append(rs.next_action.sleep)

    r = tenacity.Retrying(
        sleep=sleeps.append,
        wait=wait,
        stop=tenacity.stop_after_attempt(5),
        retry=tenacity.retry_if_result(lambda x: x is None),
        before_sleep=before_sleep,
        retry_error_callback=lambda rs: rs.attempt_number,
    )
    assert r(lambda: None) == 5
    assert sleeps == expected
    assert announced == expected
    assert all(isinstance(s, float) for s in sleeps)
    assert r.statistics["idle_for"] == pytest.approx(sum(expected))
