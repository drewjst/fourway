import asyncio
import logging

import pytest

import tenacity
from tenacity import AsyncRetrying, RetryError, Retrying, stop_after_attempt


class _Capture(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records = []

    def emit(self, record):
        self.records.append(record)


def test_sync_unchanged_sleep_accounting_consistent():
    logger = logging.getLogger("sleep_accounting_invariant_sync")
    logger.propagate = False
    logger.setLevel(logging.INFO)
    handler = _Capture()
    logger.addHandler(handler)
    sleeps = []

    def fails():
        raise ValueError("boom")

    try:
        r = Retrying(
            stop=stop_after_attempt(3),
            wait=tenacity.wait_fixed(0.5),
            before_sleep=tenacity.before_sleep_log(logger, logging.INFO),
            sleep=sleeps.append,
        )
        with pytest.raises(RetryError):
            r(fails)
    finally:
        logger.removeHandler(handler)
    assert sleeps == [0.5, 0.5]
    assert r.statistics["idle_for"] == pytest.approx(1.0)
    assert r.statistics["attempt_number"] == 3
    assert len(handler.records) == 2
    for rec in handler.records:
        assert "in 0.5 seconds" in rec.getMessage()


def test_async_unchanged_sleep_accounting_consistent():
    sleeps = []
    idle_seen = []

    async def rec(s):
        sleeps.append(s)

    async def f():
        raise ValueError("boom")

    r = AsyncRetrying(
        stop=stop_after_attempt(4),
        wait=tenacity.wait_fixed(2),
        before=lambda rs: idle_seen.append(rs.idle_for),
        before_sleep=lambda rs: None,
        sleep=rec,
    )

    async def main():
        with pytest.raises(RetryError):
            await r(f)

    asyncio.run(main())
    assert sleeps == [2, 2, 2]
    assert r.statistics["idle_for"] == sum(sleeps)
    assert idle_seen == [0, 2, 4, 6]
