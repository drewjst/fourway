import pytest
from unittest import mock

pytest.importorskip("tornado")

import tenacity
from tenacity import retry, stop_after_attempt


def test_tornado_none_decorator_enabled_false_calls_once():
    calls = []
    with mock.patch.object(tenacity, "tornado", None):

        @retry(enabled=False, stop=stop_after_attempt(3))
        def always_fails():
            calls.append(1)
            raise ValueError("fail")

        with pytest.raises(ValueError, match="fail"):
            always_fails()
    assert len(calls) == 1
    assert isinstance(always_fails.retry, tenacity.Retrying)


def test_tornado_none_decorator_retries_normally():
    calls = []
    with mock.patch.object(tenacity, "tornado", None):

        @retry(stop=stop_after_attempt(3), reraise=True, sleep=lambda s: None)
        def flaky():
            calls.append(1)
            if len(calls) < 3:
                raise ValueError("not yet")
            return "ok"

        assert flaky() == "ok"
    assert len(calls) == 3
