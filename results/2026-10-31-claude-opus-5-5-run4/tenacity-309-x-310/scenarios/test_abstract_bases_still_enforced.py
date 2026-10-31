import abc

import pytest

import tenacity
from tenacity.retry import retry_base
from tenacity.stop import stop_base
from tenacity.wait import wait_base


def test_bases_remain_abstract_with_abcmeta():
    for cls in (retry_base, stop_base, wait_base, tenacity.BaseRetrying):
        assert isinstance(cls, abc.ABCMeta)
        with pytest.raises(TypeError):
            cls()

    class Incomplete(tenacity.BaseRetrying):
        pass

    with pytest.raises(TypeError):
        Incomplete()


def test_custom_subclasses_and_combinators_drive_retrying():
    class my_retry(retry_base):
        def __call__(self, retry_state):
            return retry_state.outcome.failed

    class my_stop(stop_base):
        def __call__(self, retry_state):
            return retry_state.attempt_number >= 3

    class my_wait(wait_base):
        def __call__(self, retry_state):
            return 0.5

    sleeps = []
    calls = []

    def fn():
        calls.append(1)
        raise ValueError("boom")

    r = tenacity.Retrying(
        sleep=sleeps.append,
        retry=my_retry() | tenacity.retry_never,
        stop=my_stop() & tenacity.stop_after_attempt(2),
        wait=my_wait() + tenacity.wait_fixed(1),
    )
    with pytest.raises(tenacity.RetryError):
        r(fn)
    assert len(calls) == 3
    assert sleeps == [1.5, 1.5]
    assert r.statistics["attempt_number"] == 3
