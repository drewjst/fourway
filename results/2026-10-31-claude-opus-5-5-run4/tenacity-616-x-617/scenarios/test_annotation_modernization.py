from tenacity import AttemptManager, BaseRetrying
from tenacity.wait import wait_base


def test_attempt_manager_traceback_annotation_uses_pep604():
    assert AttemptManager.__exit__.__annotations__['traceback'] == 'types.TracebackType | None'
    assert AttemptManager.__aexit__.__annotations__['traceback'] == 'types.TracebackType | None'


def test_copy_and_radd_annotations_use_pep604():
    ann = BaseRetrying.copy.__annotations__
    assert ann['stop'] == 'StopBaseT | object'
    assert ann['wait'] == 'WaitBaseT | object'
    assert wait_base.__radd__.__annotations__['return'] == 'wait_combine | wait_base'
