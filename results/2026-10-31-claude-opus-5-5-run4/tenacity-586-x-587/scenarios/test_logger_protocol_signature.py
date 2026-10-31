import inspect

from tenacity import _utils


def test_logger_protocol_msg_is_not_positional_only():
    sig = inspect.signature(_utils.LoggerProtocol.log)
    params = sig.parameters
    assert params["level"].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    assert params["msg"].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    assert any(p.kind is inspect.Parameter.VAR_POSITIONAL for p in params.values())
    assert any(p.kind is inspect.Parameter.VAR_KEYWORD for p in params.values())


def test_logger_protocol_matches_logging_logger_msg_kind():
    import logging

    proto = inspect.signature(_utils.LoggerProtocol.log).parameters["msg"].kind
    real = inspect.signature(logging.Logger.log).parameters["msg"].kind
    assert proto == real
