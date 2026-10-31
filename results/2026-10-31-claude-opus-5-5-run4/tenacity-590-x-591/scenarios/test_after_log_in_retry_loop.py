import logging
import re

import tenacity
from tenacity import Retrying, after_log, stop_after_attempt


class FakeLogger:
    def __init__(self):
        self.calls = []

    def log(self, level, msg, *args, **kwargs):
        self.calls.append((level, msg))


def test_after_log_numeric_seconds_in_real_loop():
    logger = FakeLogger()
    sleeps = []
    counter = {"n": 0}

    def flaky():
        counter["n"] += 1
        if counter["n"] < 3:
            raise ValueError("boom")
        return "ok"

    r = Retrying(
        sleep=sleeps.append,
        stop=stop_after_attempt(5),
        wait=tenacity.wait_fixed(0),
        after=after_log(logger, logging.INFO),
    )
    assert r(flaky) == "ok"
    assert counter["n"] == 3
    assert len(logger.calls) == 2
    pat = re.compile(
        r"^Finished call to '.*flaky' after [-0-9.e+]+\(s\), this was the (1st|2nd) time calling it\.$"
    )
    for level, msg in logger.calls:
        assert level == logging.INFO
        assert pat.match(msg), msg
        assert "?(s)" not in msg
    assert logger.calls[0][1].endswith("1st time calling it.")
    assert logger.calls[1][1].endswith("2nd time calling it.")
    assert r.statistics["attempt_number"] == 3
