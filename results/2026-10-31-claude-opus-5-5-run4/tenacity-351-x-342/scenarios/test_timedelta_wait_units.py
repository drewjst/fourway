import datetime
import inspect
import random

import pytest

import tenacity
from tenacity import wait as wait_mod


def _state(n):
    rs = tenacity.RetryCallState(None, None, (), {})
    rs.attempt_number = n
    rs.set_result(None)
    return rs


def _strategies_with_max():
    out = []
    for name, obj in vars(wait_mod).items():
        if not inspect.isclass(obj):
            continue
        if obj.__module__ != wait_mod.__name__:
            continue
        if not issubclass(obj, wait_mod.wait_base) or inspect.isabstract(obj):
            continue
        try:
            params = inspect.signature(obj.__init__).parameters
        except (TypeError, ValueError):
            continue
        if "max" in params:
            out.append(obj)
    return sorted(out, key=lambda c: c.__name__)


@pytest.fixture
def seeded_random():
    state = random.getstate()
    random.seed(12345)
    try:
        yield
    finally:
        random.setstate(state)


def test_every_wait_strategy_accepts_timedelta_max(seeded_random):
    classes = _strategies_with_max()
    assert classes, "expected wait strategies with a max parameter"
    cap = datetime.timedelta(seconds=5)
    failures = []
    for cls in classes:
        try:
            strategy = cls(max=cap)
            for n in range(1, 13):
                w = strategy(retry_state=_state(n))
                assert not isinstance(w, datetime.timedelta), "returned timedelta"
                assert isinstance(w, (int, float)), "non-numeric wait %r" % (w,)
                assert 0 <= w <= 5, "wait %r exceeds cap" % (w,)
        except Exception as exc:  # noqa: B902
            failures.append("%s: %r" % (cls.__name__, exc))
    assert not failures, failures


def test_retrying_sleeps_with_timedelta_max_for_every_strategy(seeded_random):
    classes = _strategies_with_max()
    assert classes
    failures = []
    for cls in classes:
        sleeps = []
        try:
            r = tenacity.Retrying(
                sleep=sleeps.append,
                wait=cls(max=datetime.timedelta(seconds=2)),
                stop=tenacity.stop_after_attempt(4),
                retry=tenacity.retry_if_result(lambda x: True),
                retry_error_callback=lambda rs: "done",
            )
            assert r(lambda: None) == "done"
            assert len(sleeps) == 3, sleeps
            for s in sleeps:
                assert isinstance(s, float)
                assert 0 <= s <= 2, s
        except Exception as exc:  # noqa: B902
            failures.append("%s: %r" % (cls.__name__, exc))
    assert not failures, failures
