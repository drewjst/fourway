import tenacity
from tenacity import Retrying, RetryError, stop_after_attempt


def test_every_all_name_resolves():
    missing = [n for n in tenacity.__all__ if not hasattr(tenacity, n)]
    assert missing == []
    assert len(set(tenacity.__all__)) == len(tenacity.__all__)


def test_callable_wait_returning_numbers_drives_sleep():
    sleeps = []

    def my_wait(retry_state):
        if retry_state.attempt_number == 1:
            return 2
        return 0.5

    calls = []

    def fn():
        calls.append(1)
        raise ValueError("boom")

    r = Retrying(sleep=sleeps.append, wait=my_wait, stop=stop_after_attempt(3))
    try:
        r(fn)
    except RetryError as e:
        assert e.last_attempt.attempt_number == 3
    else:
        raise AssertionError("expected RetryError")
    assert len(calls) == 3
    assert sleeps == [2.0, 0.5]
    assert r.statistics["idle_for"] == 2.5
