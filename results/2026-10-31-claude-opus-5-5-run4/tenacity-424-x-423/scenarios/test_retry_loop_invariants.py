import types
from concurrent import futures

import pytest

import tenacity


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def monotonic(self):
        return self.now


@pytest.fixture
def clock(monkeypatch):
    c = FakeClock()
    monkeypatch.setattr(tenacity, "time", types.SimpleNamespace(monotonic=c.monotonic))
    return c


def test_sleep_bookkeeping_consistent(clock):
    sleeps = []
    announced = []
    wait_calls = []
    attempts = []

    def fake_sleep(s):
        sleeps.append(s)
        clock.now += s

    def my_wait(retry_state):
        wait_calls.append(retry_state.attempt_number)
        return 0.5

    def before_sleep(retry_state):
        announced.append(retry_state.next_action.sleep)

    r = tenacity.Retrying(
        sleep=fake_sleep,
        wait=my_wait,
        stop=tenacity.stop_after_attempt(4),
        before_sleep=before_sleep,
    )

    def fn():
        attempts.append(1)
        raise ValueError("x")

    with pytest.raises(tenacity.RetryError):
        r(fn)
    assert len(attempts) == 4
    assert sleeps == [0.5, 0.5, 0.5]
    assert announced == sleeps
    assert r.statistics["idle_for"] == 1.5
    assert r.statistics["attempt_number"] == 4
    # wait evaluated at most once per attempt, never duplicated
    assert len(wait_calls) == len(set(wait_calls))
    assert len(attempts) - 1 <= len(wait_calls) <= len(attempts)


def test_stop_after_delay_semantics_unchanged(clock):
    sleeps = []
    calls = []

    def fake_sleep(s):
        sleeps.append(s)
        clock.now += s

    def fn():
        calls.append(clock.now)
        raise ValueError("boom")

    r = tenacity.Retrying(
        sleep=fake_sleep,
        stop=tenacity.stop_after_delay(5),
        wait=tenacity.wait_exponential(),
        reraise=True,
    )
    with pytest.raises(ValueError):
        r(fn)
    assert calls == [0.0, 1.0, 3.0, 7.0]
    assert sleeps == [1.0, 2.0, 4.0]


def test_future_type_usable():
    assert issubclass(tenacity.Future, futures.Future)
    ok = tenacity.Future.construct(1, 5, False)
    assert ok.result() == 5 and not ok.failed
    bad = tenacity.Future.construct(2, KeyError("k"), True)
    assert bad.failed and bad.attempt_number == 2
    err = tenacity.RetryError(bad)
    with pytest.raises(KeyError):
        err.reraise()


def test_retry_error_callback_receives_last_state(clock):
    def fake_sleep(s):
        clock.now += s

    def cb(retry_state):
        return (retry_state.attempt_number, retry_state.outcome.failed)

    r = tenacity.Retrying(
        sleep=fake_sleep,
        stop=tenacity.stop_after_attempt(3),
        wait=tenacity.wait_fixed(1),
        retry_error_callback=cb,
    )

    def fn():
        raise ValueError("x")

    assert r(fn) == (3, True)
    assert clock.now == 2.0
