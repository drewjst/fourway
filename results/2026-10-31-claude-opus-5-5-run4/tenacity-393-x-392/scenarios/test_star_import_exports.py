import pytest

import tenacity


def _star_namespace():
    ns = {}
    exec("from tenacity import *", ns)
    return ns


def test_all_lists_new_names():
    assert "retry_if_exception_cause_type" in tenacity.__all__
    assert "wait_exponential_jitter" in tenacity.__all__


def test_star_import_exposes_and_works():
    ns = _star_namespace()
    assert "retry_if_exception_cause_type" in ns
    assert "wait_exponential_jitter" in ns
    assert ns["wait_exponential_jitter"] is tenacity.wait.wait_exponential_jitter
    assert ns["retry_if_exception_cause_type"] is tenacity.retry.retry_if_exception_cause_type

    sleeps = []
    calls = []

    def fn():
        calls.append(1)
        if len(calls) < 3:
            try:
                raise NameError("inner")
            except NameError as e:
                raise IOError("outer") from e
        return "ok"

    r = ns["Retrying"](
        sleep=sleeps.append,
        wait=ns["wait_exponential_jitter"](initial=1, max=1, jitter=0),
        retry=ns["retry_if_exception_cause_type"](NameError),
        stop=ns["stop_after_attempt"](5),
    )
    assert r(fn) == "ok"
    assert len(calls) == 3
    assert sleeps == [1.0, 1.0]
