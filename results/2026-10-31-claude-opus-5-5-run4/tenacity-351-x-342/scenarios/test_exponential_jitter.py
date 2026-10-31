import random

import pytest

import tenacity


def _state(n):
    rs = tenacity.RetryCallState(None, None, (), {})
    rs.attempt_number = n
    rs.set_result(None)
    return rs


def test_exponential_jitter_growth_cap_and_combination():
    fn = tenacity.wait.wait_exponential_jitter(initial=1, max=10, jitter=0)
    expected = [1, 2, 4, 8, 10, 10]
    got = [fn(retry_state=_state(n)) for n in range(1, 7)]
    assert got == expected
    combined = fn + tenacity.wait_fixed(2)
    got_combined = [combined(retry_state=_state(n)) for n in range(1, 7)]
    assert got_combined == [e + 2 for e in expected]


def test_exponential_jitter_drives_retrying_sleeps():
    state = random.getstate()
    random.seed(7)
    try:
        sleeps = []
        calls = []

        def fail():
            calls.append(1)
            raise ValueError("boom")

        r = tenacity.Retrying(
            sleep=sleeps.append,
            wait=tenacity.wait_exponential_jitter(initial=0.5, max=3, jitter=0.25),
            stop=tenacity.stop_after_attempt(5),
            retry=tenacity.retry_if_exception_type(ValueError),
            reraise=True,
        )
        with pytest.raises(ValueError):
            r(fail)
    finally:
        random.setstate(state)
    assert len(calls) == 5
    assert len(sleeps) == 4
    bounds = [(0.5, 0.75), (1.0, 1.25), (2.0, 2.25), (3.0, 3.0)]
    for s, (lo, hi) in zip(sleeps, bounds):
        assert isinstance(s, float)
        assert lo <= s <= hi, (s, lo, hi)
