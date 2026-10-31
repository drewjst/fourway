import pytest

import tenacity
from tenacity import Retrying, RetryError, stop_after_attempt, wait_fixed


def test_context_manager_records_exceptions_and_retries():
    sleeps = []
    attempts = []
    r = Retrying(stop=stop_after_attempt(3), wait=wait_fixed(0.5), sleep=sleeps.append)
    with pytest.raises(RetryError) as ei:
        for attempt in r:
            with attempt:
                attempts.append(attempt.retry_state.attempt_number)
                raise ValueError('boom')
    assert attempts == [1, 2, 3]
    assert sleeps == [0.5, 0.5]
    last = ei.value.last_attempt
    assert last.failed
    assert isinstance(last.exception(), ValueError)
    assert last.attempt_number == 3


def test_copy_preserves_stop_wait_and_sum_of_waits():
    stop = stop_after_attempt(2)
    w = sum([wait_fixed(1), wait_fixed(2)])
    r = Retrying(stop=stop, wait=w, sleep=lambda s: None)
    c = r.copy()
    assert c.stop is stop
    assert c.wait is w
    sleeps = []
    c2 = r.copy(sleep=sleeps.append, stop=stop_after_attempt(3))
    calls = []

    def f():
        calls.append(1)
        raise KeyError('x')

    with pytest.raises(KeyError):
        c2.copy(reraise=True)(f)
    assert len(calls) == 3
    with pytest.raises(RetryError):
        c2(f)
    assert sleeps[-2:] == [3.0, 3.0]
