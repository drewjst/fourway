import pytest

from tinydb import TinyDB, where
from tinydb.storages import MemoryStorage, JSONStorage
from tinydb.table import Document


@pytest.fixture(params=['memory', 'json'])
def table(request, tmp_path):
    if request.param == 'json':
        db = TinyDB(str(tmp_path / 'db.json'), storage=JSONStorage)
    else:
        db = TinyDB(storage=MemoryStorage)
    yield db.table('t')
    db.close()


def _fresh(table, value):
    return len([d for d in table.all() if d.get('int') == value])


def _check(table, queries):
    for value, query in queries:
        expected = _fresh(table, value)
        assert table.count(query) == expected
        assert len(table.search(query)) == expected
        assert table.count(query) == expected


def test_count_tracks_mixed_writes(table):
    q1 = where('int') == 1
    q2 = where('int') == 2
    queries = [(1, q1), (2, q2)]
    _check(table, queries)

    first = table.insert({'int': 1})
    _check(table, queries)

    table.insert(Document({'int': 2}, 10))
    _check(table, queries)

    table.insert({'int': 3})
    _check(table, queries)

    table.update({'int': 2}, doc_ids=[first])
    _check(table, queries)
    assert table.count(q2) == 2
    assert table.count(q1) == 0

    table.remove(q2)
    _check(table, queries)

    table.insert({'int': 1})
    _check(table, queries)
    assert table.count(q1) == 1


def test_failed_duplicate_insert_leaves_count_unchanged(table):
    query = where('int') == 1
    assert table.insert({'int': 1}) == 1
    assert table.count(query) == 1

    with pytest.raises(ValueError):
        table.insert(Document({'int': 1}, 1))

    assert table.count(query) == 1
    assert len(table) == 1
    assert len(table.search(query)) == 1


def test_failed_write_on_read_only_storage_leaves_count_unchanged(tmp_path):
    path = str(tmp_path / 'ro.json')
    db = TinyDB(path, storage=JSONStorage)
    db.insert({'int': 1})
    db.insert({'int': 2})
    db.close()

    db = TinyDB(path, storage=JSONStorage, access_mode='r')
    query = where('int') == 1
    assert db.count(query) == 1

    with pytest.raises(IOError):
        db.insert({'int': 1})

    assert db.count(query) == 1
    assert len(db.search(query)) == 1
    assert len(db) == 2
    db.close()
