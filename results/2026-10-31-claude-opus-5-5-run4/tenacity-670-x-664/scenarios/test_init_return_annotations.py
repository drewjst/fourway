import inspect

import tenacity
from tenacity import AttemptManager, BaseRetrying, RetryCallState, Retrying


def test_attempt_manager_init_returns_none_annotation():
    sig = inspect.signature(AttemptManager.__init__)
    assert sig.return_annotation is None


def test_base_retrying_init_returns_none_annotation_and_constructs():
    sig = inspect.signature(BaseRetrying.__init__)
    assert sig.return_annotation is None
    r = Retrying(name="blk", before_sleep=None)
    rs = RetryCallState(r, None, (), {})
    am = AttemptManager(rs)
    assert am.retry_state is rs
    assert str(r) == "blk"
