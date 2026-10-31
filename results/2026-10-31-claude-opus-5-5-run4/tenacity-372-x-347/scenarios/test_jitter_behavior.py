import random

import tenacity
from tenacity import RetryCallState


def _state(attempt):
    rs = RetryCallState(None, None, (), {})
    rs.attempt_number = attempt
    rs.set_result(None)
    return rs


def test_jitter_is_additive_not_multiplied(monkeypatch):
    monkeypatch.setattr(random, "uniform", lambda a, b: b)
    w = tenacity.wait_exponential_jitter(initial=10, jitter=1, max=1000)
    assert w(_state(1)) == 11
    assert w(_state(2)) == 21
    assert w(_state(3)) == 41


def test_jitter_respects_max_in_retrying(monkeypatch):
    monkeypatch.setattr(random, "uniform", lambda a, b: b)
    sleeps = []
    r = tenacity.Retrying(
        sleep=sleeps.append,
        wait=tenacity.wait_exponential_jitter(initial=10, jitter=1, max=25),
        stop=tenacity.stop_after_attempt(4),
    )

    def always_fail():
        raise ValueError("boom")

    try:
        r(always_fail)
    except tenacity.RetryError:
        pass
    else:
        raise AssertionError("expected RetryError")
    assert sleeps == [11.0, 21.0, 25.0]
