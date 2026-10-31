import pytest

import tenacity
from tenacity import RetryError, Retrying, TryAgain


def test_callback_order_and_statistics():
    events = []

    def before(rs):
        events.append(("before", rs.attempt_number))

    def after(rs):
        events.append(("after", rs.attempt_number))

    def before_sleep(rs):
        events.append(("before_sleep", rs.attempt_number, rs.next_action.sleep, rs.upcoming_sleep))

    def sleep(s):
        events.append(("sleep", float(s)))

    r = Retrying(
        sleep=sleep,
        wait=tenacity.wait_fixed(1.5),
        stop=tenacity.stop_after_attempt(3),
        before=before,
        after=after,
        before_sleep=before_sleep,
    )

    def fn():
        raise ValueError("x")

    with pytest.raises(RetryError) as ei:
        r(fn)
    assert events == [
        ("before", 1),
        ("after", 1),
        ("before_sleep", 1, 1.5, 1.5),
        ("sleep", 1.5),
        ("before", 2),
        ("after", 2),
        ("before_sleep", 2, 1.5, 1.5),
        ("sleep", 1.5),
        ("before", 3),
        ("after", 3),
    ]
    assert r.statistics["attempt_number"] == 3
    assert r.statistics["idle_for"] == 3.0
    assert ei.value.last_attempt.attempt_number == 3
    assert isinstance(ei.value.__cause__, ValueError)


def test_try_again_skips_predicate_and_stop_sees_wait():
    pred_calls = []
    stop_seen = []

    def pred(rs):
        pred_calls.append(rs.attempt_number)
        return False

    def stop(rs):
        stop_seen.append(rs.upcoming_sleep)
        return rs.attempt_number >= 5

    attempts = [0]

    def fn():
        attempts[0] += 1
        if attempts[0] < 3:
            raise TryAgain
        return "ok"

    r = Retrying(sleep=lambda s: None, retry=pred, stop=stop, wait=tenacity.wait_fixed(2))
    assert r(fn) == "ok"
    assert attempts[0] == 3
    assert pred_calls == [3]
    assert stop_seen == [2.0, 2.0]


def test_retry_error_callback_and_reraise():
    cb_calls = []

    def cb(rs):
        cb_calls.append(rs.attempt_number)
        return "fallback"

    calls = []

    def fn():
        calls.append(1)
        raise KeyError("bad")

    r = Retrying(sleep=lambda s: None, stop=tenacity.stop_after_attempt(2), retry_error_callback=cb)
    assert r(fn) == "fallback"
    assert cb_calls == [2]
    assert len(calls) == 2

    calls.clear()
    r2 = Retrying(sleep=lambda s: None, stop=tenacity.stop_after_attempt(2), reraise=True)
    with pytest.raises(KeyError):
        r2(fn)
    assert len(calls) == 2
