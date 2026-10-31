import pytest

import tenacity
from tenacity import Retrying


def test_empty_message_retries_bare_exceptions_with_exponential_wait():
    sleeps = []
    calls = {"n": 0}

    def fn():
        calls["n"] += 1
        if calls["n"] <= 3:
            raise RuntimeError()
        return "ok"

    r = Retrying(
        sleep=sleeps.append,
        stop=tenacity.stop_after_attempt(5),
        retry=tenacity.retry_if_exception_message(message=""),
        wait=tenacity.wait_exponential(multiplier=1, max=40),
    )
    assert r(fn) == "ok"
    assert calls["n"] == 4
    assert sleeps == [1, 2, 4]


def test_not_empty_message_stops_on_bare_exception_with_capped_wait():
    sleeps = []
    calls = {"n": 0}

    def fn():
        calls["n"] += 1
        if calls["n"] <= 2:
            raise RuntimeError("boom")
        raise RuntimeError()

    r = Retrying(
        sleep=sleeps.append,
        stop=tenacity.stop_after_attempt(10),
        retry=tenacity.retry_if_not_exception_message(message=""),
        wait=tenacity.wait_exponential(multiplier=100, max=40),
        reraise=True,
    )
    with pytest.raises(RuntimeError) as excinfo:
        r(fn)
    assert str(excinfo.value) == ""
    assert calls["n"] == 3
    assert sleeps == [40, 40]
