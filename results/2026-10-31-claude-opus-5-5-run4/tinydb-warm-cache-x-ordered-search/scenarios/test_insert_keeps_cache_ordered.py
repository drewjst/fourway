from tinydb import TinyDB, where
from tinydb.storages import MemoryStorage
from tinydb.table import Document


def test_insert_appends_to_cached_search_without_rescan():
    db = TinyDB(storage=MemoryStorage)
    table = db.table('t')
    table.insert(Document({'int': 1}, doc_id=4))
    table.insert(Document({'int': 1}, doc_id=2))
    query = where('int') == 1
    first = table.search(query)
    assert sorted(d.doc_id for d in first) == [2, 4]

    new_id = table.insert({'int': 1})
    assert new_id == 5
    assert query in table._query_cache

    table._read_table = lambda: {}
    result = table.search(query)
    assert len(result) == 3
    assert result[-1].doc_id == 5


def test_insert_keeps_non_matching_cached_search():
    db = TinyDB(storage=MemoryStorage)
    db.insert(Document({'int': 1}, doc_id=9))
    query = where('int') == 2
    assert db.search(query) == []

    db.insert({'int': 1})

    assert query in db._query_cache
    assert db.search(query) == []
