import typing
from typing import Callable, Mapping, Any, Union

from tinydb import TinyDB, where
from tinydb.storages import MemoryStorage
from tinydb import operations


def test_operation_type_hints_present():
    ret = Callable[[Mapping], None]
    for name in ('delete', 'add', 'subtract', 'set', 'increment', 'decrement'):
        hints = typing.get_type_hints(getattr(operations, name))
        assert hints['return'] == ret, name
        assert hints['field'] is str, name
    assert typing.get_type_hints(operations.add)['n'] == Union[int, float]
    assert typing.get_type_hints(operations.subtract)['n'] == Union[int, float]
    assert typing.get_type_hints(operations.set)['val'] == Any


def test_annotated_operations_apply_via_update():
    hints = typing.get_type_hints(operations.increment)
    assert 'return' in hints
    db = TinyDB(storage=MemoryStorage)
    db.insert_multiple([{'n': 1}, {'n': 5}])
    assert db.update(operations.add('n', 10), doc_ids=[2]) == [2]
    assert db.update(operations.decrement('n'), where('n') == 1) == [1]
    assert db.get(doc_id=1)['n'] == 0
    assert db.get(doc_id=2)['n'] == 15
