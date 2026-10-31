import pytest

import tenacity
from tenacity import RetryError, Retrying


class ExplodingPower(float):
    def __pow__(self, exponent, modulo=None):
        raise AssertionError("power should not be computed once the cap is reached")


def test_capped_wait_skips_power_in_message_filtered_loop():
    sleeps = []
    calls = {"n": 0}

    def fn():
        calls["n"] += 1
        raise ValueError("transient failure")

    r = Retrying(
        sleep=sleeps.append,
        stop=tenacity.stop_after_attempt(4),
        retry=tenacity.retry_if_exception_message(match="trans.*"),
        wait=tenacity.wait_exponential(
            multiplier=100, max=40, exp_base=ExplodingPower(2)
        ),
    )
    with pytest.raises(RetryError):
        r(fn)
    assert calls["n"] == 4
    assert sleeps == [40.0, 40.0, 40.0]
    assert r.statistics["idle_for"] == 120.0


def test_random_exponential_cap_skips_power_with_not_message_retry():
    sleeps = []
    calls = {"n": 0}

    def fn():
        calls["n"] += 1
        if calls["n"] < 4:
            raise ValueError("transient")
        return "done"

    r = Retrying(
        sleep=sleeps.append,
        stop=tenacity.stop_after_attempt(10),
        retry=tenacity.retry_if_not_exception_message(match="fatal"),
        wait=tenacity.wait_random_exponential(
            multiplier=100, max=40, min=40, exp_base=ExplodingPower(2)
        ),
    )
    assert r(fn) == "done"
    assert calls["n"] == 4
    assert sleeps == [40.0, 40.0, 40.0]
