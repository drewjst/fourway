import sys
import threading

import pytest

import tenacity
from tenacity import RetryCallState, RetryError, Retrying


def _set_exc(rs, exc):
    try:
        raise exc
    except BaseException:
        rs.set_exception(sys.exc_info())


def test_iter_state_flags_track_decisions():
    r = Retrying(
        sleep=lambda s: None,
        stop=tenacity.stop_after_attempt(2),
        retry=tenacity.retry_if_exception_type(ValueError),
    )
    assert isinstance(r.iter_state, tenacity.IterState)
    r.begin()
    rs = RetryCallState(r, fn=None, args=(), kwargs={})

    assert isinstance(r.iter(rs), tenacity.DoAttempt)
    _set_exc(rs, tenacity.TryAgain())
    do = r.iter(rs)
    assert isinstance(do, tenacity.DoSleep)
    assert r.iter_state.is_explicit_retry is True
    assert r.iter_state.stop_run_result is False

    rs.prepare_for_next_attempt()
    assert isinstance(r.iter(rs), tenacity.DoAttempt)
    _set_exc(rs, ValueError("boom"))
    with pytest.raises(RetryError):
        r.iter(rs)
    assert r.iter_state.is_explicit_retry is False
    assert r.iter_state.retry_run_result is True
    assert r.iter_state.stop_run_result is True


def test_iter_state_is_thread_local():
    r = Retrying()
    main_state = r.iter_state
    assert isinstance(main_state, tenacity.IterState)
    other = []

    def worker():
        other.append(r.iter_state)
        r(lambda: 42)

    t = threading.Thread(target=worker)
    t.start()
    t.join()
    assert len(other) == 1
    assert isinstance(other[0], tenacity.IterState)
    assert other[0] is not main_state
    assert r.iter_state is main_state
