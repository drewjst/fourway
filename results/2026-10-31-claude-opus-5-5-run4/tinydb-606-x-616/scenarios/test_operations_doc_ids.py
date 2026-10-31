import pytest

from tinydb import TinyDB, where
from tinydb.storages import MemoryStorage, JSONStorage
from tinydb.operations import increment, delete, set as op_set


@pytest.fixture(params=['memory', 'json'])
def db(request, tmp_path):
    if request.param == 'json':
        db_ = TinyDB(str(tmp_path / 'ops.json'), storage=JSONStorage)
    else:
        db_ = TinyDB(storage=MemoryStorage)
    db_.drop_tables()
    db_.insert_multiple({'int': 1, 'char': c} for c in 'abc')
    yield db_
    db_.close()


def test_increment_mixed_doc_ids_is_atomic_and_filtered(db):
    result = db.update(increment('int'), doc_ids=[1, 99])
    assert sorted(result) == [1]
    assert db.get(doc_id=1)['int'] == 2
    assert db.get(doc_id=2)['int'] == 1
    assert db.get(doc_id=3)['int'] == 1
    assert db.count(where('int') == 2) == 1


def test_delete_and_set_with_missing_doc_ids(db):
    assert db.update(delete('char'), doc_ids=[42]) == []
    assert db.count(where('char').exists()) == 3
    assert sorted(db.update(op_set('char', 'z'), doc_ids=[77, 2])) == [2]
    assert db.get(doc_id=2)['char'] == 'z'
    assert db.get(doc_id=1)['char'] == 'a'
    assert db.get(doc_id=3)['char'] == 'c'
