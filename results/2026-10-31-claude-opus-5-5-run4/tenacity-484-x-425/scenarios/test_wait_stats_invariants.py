import random

import pytest

from tenacity import RetryError, retry, stop_after_attempt, wait_random_exponential


def test_random_exponential_bounded_by_max_through_decorator(monkeypatch):
    sleeps = []

    @retry(
        sleep=lambda s: sleeps.append(float(s)),
        stop=stop_after_attempt(10),
        wait=wait_random_exponential(multiplier=1, max=8),
    )
    def f():
        raise ValueError("boom")

    for picker in (lambda a, b: a, lambda a, b: b):
        sleeps.clear()
        monkeypatch.setattr(random, "uniform", picker)
        with pytest.raises(RetryError):
            f()
        assert len(sleeps) == 9
        for s in sleeps:
            assert 0.0 <= s <= 8.0


def test_statistics_reflect_latest_run_and_sleeps():
    sleeps = []
    calls = {"n": 0, "fail_until": 0}

    @retry(
        sleep=lambda s: sleeps.append(float(s)),
        stop=stop_after_attempt(6),
        wait=wait_random_exponential(multiplier=1, max=20),
    )
    def f():
        calls["n"] += 1
        if calls["n"] <= calls["fail_until"]:
            raise ValueError("boom")
        return "ok"

    state = random.getstate()
    random.seed(42)
    try:
        calls.update(n=0, fail_until=3)
        assert f() == "ok"
        assert f.statistics["attempt_number"] == 4
        assert f.statistics["idle_for"] == pytest.approx(sum(sleeps))
        assert len(sleeps) == 3

        sleeps.clear()
        calls.update(n=0, fail_until=1)
        assert f() == "ok"
        assert f.statistics["attempt_number"] == 2
        assert f.statistics["idle_for"] == pytest.approx(sum(sleeps))
        assert len(sleeps) == 1
    finally:
        random.setstate(state)
