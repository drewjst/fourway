import random

import pytest

from tenacity import RetryError, retry, stop_after_attempt, wait_fixed, wait_random_exponential


def test_decorated_random_exponential_respects_min(monkeypatch):
    sleeps = []

    @retry(
        sleep=lambda s: sleeps.append(float(s)),
        stop=stop_after_attempt(4),
        wait=wait_random_exponential(multiplier=1, min=2, max=10),
    )
    def f():
        raise ValueError("boom")

    # Always pick the lower bound of the sampled interval.
    monkeypatch.setattr(random, "uniform", lambda a, b: a)

    with pytest.raises(RetryError):
        f()

    assert sleeps == [2.0, 2.0, 2.0]
    assert f.statistics["attempt_number"] == 4
    assert f.statistics["idle_for"] == pytest.approx(6.0)


def test_retry_with_random_exponential_min_seeded():
    sleeps = []

    @retry(sleep=lambda s: sleeps.append(float(s)), stop=stop_after_attempt(3), wait=wait_fixed(0))
    def f():
        raise ValueError("boom")

    state = random.getstate()
    random.seed(1234)
    try:
        g = f.retry_with(
            stop=stop_after_attempt(40),
            wait=wait_random_exponential(multiplier=1, min=5, max=60),
        )
        with pytest.raises(RetryError):
            g()
    finally:
        random.setstate(state)

    assert len(sleeps) == 39
    for s in sleeps:
        assert 5.0 <= s <= 60.0
