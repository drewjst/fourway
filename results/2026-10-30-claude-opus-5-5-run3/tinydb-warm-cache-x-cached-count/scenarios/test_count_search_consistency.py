import pytest

from tinydb import TinyDB, where
from tinydb.storages import MemoryStorage, JSONStorage
from tinydb.table import Document


@pytest.fixture(params=['memory', 'json'])
def db(request, tmp_path):
    if request.param == 'json':
        d = TinyDB(str(tmp_path / 'db.json'), storage=JSONStorage)
    else:
        d = TinyDB(storage=MemoryStorage)
    yield d
    d.close()


def test_count_matches_search_after_inserts(db):
    db.insert({'int': 1})
    db.insert({'int': 2})
    q1 = where('int') == 1
    q3 = where('int') == 3
    assert db.count(q1) == 1
    assert db.count(q3) == 0

    db.insert({'int': 1})
    db.insert({'int': 3})
    db.insert({'int': 5})

    assert db.count(q1) == 2
    assert db.count(q3) == 1
    assert db.count(q1) == len(db.search(q1))
    assert db.count(q3) == len(db.search(q3))
    assert db.search(q1) == [{'int': 1}, {'int': 1}]

    small = db.table('small', cache_size=1)
    small.insert({'int': 1})
    assert small.count(q1) == 1
    assert small.count(q3) == 0
    small.insert({'int': 1})
    small.insert({'int': 3})
    assert small.count(q1) == 2
    assert small.count(q3) == 1
    assert small.count(q1) == len(small.search(q1))


def test_failed_insert_leaves_count_unchanged(db):
    db.insert({'int': 1})
    query = where('int') == 1
    assert db.count(query) == 1

    with pytest.raises(ValueError):
        db.insert(Document({'int': 1}, 1))

    assert db.count(query) == 1
    assert len(db.search(query)) == 1
    assert len(db) == 1


def test_count_reflects_update_and_remove_after_insert(db):
    db.insert({'int': 1})
    query = where('int') == 1
    assert db.count(query) == 1

    db.insert({'int': 1})
    assert db.count(query) == 2

    db.update({'int': 2}, doc_ids=[1])
    assert db.count(query) == 1
    assert db.count(where('int') == 2) == 1

    db.insert({'int': 1})
    assert db.count(query) == 2

    db.remove(query)
    assert db.count(query) == 0
    assert db.search(query) == []
