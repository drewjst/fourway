import logging

from tenacity import RetryCallState, after_log


class FakeLogger:
    def __init__(self):
        self.calls = []

    def log(self, level, msg, *args, **kwargs):
        self.calls.append((level, msg))


def _state_without_timestamp(attempt):
    rs = RetryCallState(None, None, (), {})
    rs.attempt_number = attempt
    rs.set_result(None)
    rs.outcome_timestamp = None
    assert rs.seconds_since_start is None
    return rs


def test_after_log_default_format_none_seconds():
    logger = FakeLogger()
    fn = after_log(logger, logging.INFO)
    fn(_state_without_timestamp(2))
    assert logger.calls == [
        (
            logging.INFO,
            "Finished call to '<unknown>' after ?(s), this was the 2nd time calling it.",
        )
    ]


def test_after_log_custom_format_none_seconds():
    logger = FakeLogger()
    fn = after_log(logger, logging.WARNING, sec_format="%.1f")
    fn(_state_without_timestamp(3))
    assert len(logger.calls) == 1
    level, msg = logger.calls[0]
    assert level == logging.WARNING
    assert "after ?(s)" in msg
    assert msg.endswith("this was the 3rd time calling it.")
