import pytest

import tenacity
from tenacity import RetryError, Retrying, retry, stop_after_attempt


def test_enabled_direct_call_still_retries():
    calls = []

    def fails():
        calls.append(1)
        raise ValueError("fail")

    r = Retrying(stop=stop_after_attempt(3), sleep=lambda s: None)
    with pytest.raises(RetryError):
        r(fails)
    assert len(calls) == 3
    assert r.statistics["attempt_number"] == 3


def test_disabled_decorator_calls_once():
    calls = []

    @retry(enabled=False, stop=stop_after_attempt(3))
    def fails():
        calls.append(1)
        raise ValueError("fail")

    with pytest.raises(ValueError, match="fail"):
        fails()
    assert len(calls) == 1
