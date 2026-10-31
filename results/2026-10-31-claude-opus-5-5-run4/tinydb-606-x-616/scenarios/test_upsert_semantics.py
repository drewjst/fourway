import pytest

from tinydb import TinyDB, where
from tinydb.storages import MemoryStorage, JSONStorage
from tinydb.table import Document


@pytest.fixture(params=['memory', 'json'])
def db(request, tmp_path):
    if request.param == 'json':
        db_ = TinyDB(str(tmp_path / 'upsert.json'), storage=JSONStorage)
    else:
        db_ = TinyDB(storage=MemoryStorage)
    db_.drop_tables()
    db_.insert_multiple({'int': 1, 'char': c} for c in 'abc')
    yield db_
    db_.close()


def test_upsert_query_updates_all_matches_or_inserts(db):
    ids = db.upsert({'flag': True}, where('int') == 1)
    assert sorted(ids) == [1, 2, 3]
    assert db.count(where('flag') == True) == 3  # noqa
    assert len(db) == 3

    ids = db.upsert({'int': 7, 'char': 'q'}, where('char') == 'q')
    assert ids == [4]
    assert len(db) == 4
    assert db.get(doc_id=4) == {'int': 7, 'char': 'q'}


def test_upsert_document_existing_and_missing_id(db):
    assert db.upsert(Document({'char': 'v'}, doc_id=2)) == [2]
    assert db.get(doc_id=2)['char'] == 'v'
    assert len(db) == 3

    assert db.upsert(Document({'int': 5, 'char': 'w'}, doc_id=10)) == [10]
    assert db.get(doc_id=10) == {'int': 5, 'char': 'w'}
    assert len(db) == 4
    assert db.insert({'next': True}) == 11
