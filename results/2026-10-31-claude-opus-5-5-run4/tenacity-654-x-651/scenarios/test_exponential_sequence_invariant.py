import pytest

import tenacity
from tenacity import RetryError, Retrying


def _run(wait, stop_after):
    sleeps = []
    calls = {"n": 0}

    def fn():
        calls["n"] += 1
        raise ValueError("boom")

    r = Retrying(
        sleep=sleeps.append,
        stop=tenacity.stop_after_attempt(stop_after),
        retry=tenacity.retry_if_exception_message(message="boom"),
        wait=wait,
    )
    with pytest.raises(RetryError) as excinfo:
        r(fn)
    return r, sleeps, calls["n"], excinfo.value


def test_exponential_sequence_reaches_and_holds_cap():
    r, sleeps, n, err = _run(tenacity.wait_exponential(max=40), 10)
    assert n == 10
    assert sleeps == [1, 2, 4, 8, 16, 32, 40, 40, 40]
    assert r.statistics["idle_for"] == sum(sleeps)
    assert r.statistics["attempt_number"] == 10
    assert err.last_attempt.attempt_number == 10


def test_exponential_sequence_with_min_floor_and_cap():
    r, sleeps, n, _ = _run(tenacity.wait_exponential(min=10, max=100), 10)
    assert n == 10
    assert sleeps == [10, 10, 10, 10, 16, 32, 64, 100, 100]
    assert r.statistics["idle_for"] == sum(sleeps)
