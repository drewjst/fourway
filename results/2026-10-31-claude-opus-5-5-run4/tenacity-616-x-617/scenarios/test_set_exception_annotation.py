import typing

from tenacity import RetryCallState


def test_set_exception_traceback_annotation_spacing():
    ann = RetryCallState.set_exception.__annotations__['exc_info']
    args = typing.get_args(ann)
    assert len(args) == 3
    assert args[0] == type[BaseException]
    assert args[1] is BaseException
    assert args[2] == 'types.TracebackType | None'
