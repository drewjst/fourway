import asyncio
import logging

import tenacity
from tenacity import AsyncRetrying, Retrying


class _Capture(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records = []

    def emit(self, record):
        self.records.append(record)


def _logger(name):
    logger = logging.getLogger(name)
    logger.propagate = False
    logger.setLevel(logging.DEBUG)
    for h in list(logger.handlers):
        logger.removeHandler(h)
    handler = _Capture()
    logger.addHandler(handler)
    return logger, handler


def test_sync_retry_logs_each_attempt_once_with_real_logger():
    logger, handler = _logger("tenacity_merge_sync")
    calls = []

    def f():
        calls.append(1)
        if len(calls) < 3:
            raise OSError("io")
        return 42

    r = Retrying(
        sleep=lambda s: None,
        wait=tenacity.wait_fixed(0.5),
        stop=tenacity.stop_after_attempt(5),
        before=tenacity.before_log(logger, logging.INFO),
        after=tenacity.after_log(logger, logging.INFO),
        before_sleep=tenacity.before_sleep_log(logger, logging.WARNING),
    )
    assert r(f) == 42
    msgs = [rec.getMessage() for rec in handler.records]
    assert sum(m.startswith("Starting call") for m in msgs) == 1
    assert sum(m.startswith("Finished call") for m in msgs) == 2
    retrying = [m for m in msgs if m.startswith("Retrying")]
    assert len(retrying) == 2
    assert all("in 0.5 seconds as it raised OSError: io" in m for m in retrying)
    assert r.statistics["attempt_number"] == 3
    assert r.statistics["idle_for"] == 1.0
    assert r.statistics["delay_since_first_attempt"] >= 0


def test_async_retry_logs_and_records_delay_with_real_logger():
    logger, handler = _logger("tenacity_merge_async")
    calls = []
    slept = []

    async def fake_sleep(s):
        slept.append(s)

    async def f():
        calls.append(1)
        if len(calls) < 2:
            raise OSError("io")
        return "done"

    r = AsyncRetrying(
        sleep=fake_sleep,
        wait=tenacity.wait_fixed(0.25),
        stop=tenacity.stop_after_attempt(4),
        before_sleep=tenacity.before_sleep_log(logger, logging.INFO),
    )
    result = asyncio.run(r(f))
    assert result == "done"
    assert slept == [0.25]
    msgs = [rec.getMessage() for rec in handler.records]
    assert len(msgs) == 1 and msgs[0].startswith("Retrying")
    assert r.statistics["attempt_number"] == 2
    assert r.statistics["delay_since_first_attempt"] >= 0
