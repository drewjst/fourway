import abc

import tenacity
from tenacity.retry import retry_base
from tenacity.stop import stop_base
from tenacity.wait import wait_base


def test_strategy_bases_inherit_abc():
    for cls in (retry_base, stop_base, wait_base):
        assert abc.ABC in cls.__mro__, cls


def test_base_retrying_inherits_abc():
    assert abc.ABC in tenacity.BaseRetrying.__mro__
    assert abc.ABC in tenacity.Retrying.__mro__
