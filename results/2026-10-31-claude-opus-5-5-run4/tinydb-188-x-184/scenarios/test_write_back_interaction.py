import pytest

from tinydb import TinyDB, where
from tinydb.storages import MemoryStorage


def _make_db():
    db = TinyDB(storage=MemoryStorage)
    db.purge_tables()
    db.insert_multiple({'int': 1, 'char': c} for c in 'abc')
    return db


def test_write_back_invalidates_query_cache():
    db = _make_db()
    # Prime the query cache
    assert db.count(where('int') == 1) == 3

    docs = db.search(where('int') == 1)
    for d in docs:
        d['int'] = 5

    ids = db.write_back(docs)
    assert sorted(ids) == [1, 2, 3]

    # Cached result must not be served after write_back
    assert db.count(where('int') == 1) == 0
    assert db.count(where('int') == 5) == 3
    assert len(db) == 3


def test_write_back_named_table_with_ids():
    db = _make_db()
    table = db.table('other')
    table.insert_multiple({'int': 1, 'char': c} for c in 'abc')

    assert table.write_back([{'x': 1}, {'x': 2}], [1, 3]) == [1, 3]

    assert table.get(doc_id=1) == {'x': 1}
    assert table.get(doc_id=3) == {'x': 2}
    assert table.get(doc_id=2)['char'] == 'b'
    assert len(table) == 3

    # Default table untouched
    assert db.count(where('int') == 1) == 3
    assert db.tables() == {'_default', 'other'}

    # IDs keep increasing after write_back
    assert table.insert({'new': True}) == 4


def test_write_back_deprecated_eids():
    db = _make_db()
    with pytest.warns(DeprecationWarning):
        result = db.write_back([{'y': 1}], eids=[1])
    assert result == [1]
    assert db.get(doc_id=1) == {'y': 1}
    assert db.get(doc_id=1).doc_id == 1


def test_write_back_length_mismatch_does_not_modify():
    db = _make_db()
    with pytest.raises(ValueError):
        db.write_back([{'get': 'error'}], [1, 2])
    assert db.count(where('int') == 1) == 3
