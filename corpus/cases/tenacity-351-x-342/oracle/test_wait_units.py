import inspect
from datetime import timedelta

import pytest

import tenacity
from tenacity import RetryError, Retrying, wait


def strategies_with_a_max():
    found = []
    for name, cls in vars(wait).items():
        if inspect.isclass(cls) and issubclass(cls, wait.wait_base) and cls is not wait.wait_base:
            if "max" in inspect.signature(cls.__init__).parameters:
                found.append(cls)
    return found


def always_fails():
    raise ValueError("boom")


def test_every_wait_strategy_accepts_a_timedelta_max():
    for cls in strategies_with_a_max():
        sleeps = []
        r = Retrying(
            wait=cls(max=timedelta(seconds=5)),
            stop=tenacity.stop_after_attempt(4),
            sleep=sleeps.append,
        )
        with pytest.raises(RetryError):
            r(always_fails)
        assert len(sleeps) == 3, cls.__name__
        assert all(0 <= s <= 5 for s in sleeps), cls.__name__
