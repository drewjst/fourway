from tinydb import TinyDB, where
from tinydb.storages import MemoryStorage
from tinydb.table import Document


def test_explicit_id_insert_keeps_and_extends_cache():
    db = TinyDB(storage=MemoryStorage)
    db.insert(Document({'int': 1}, doc_id=5))
    query = where('int') == 1
    db.search(query)

    db.insert(Document({'int': 1}, doc_id=2))

    assert query in db._query_cache
    assert sorted(d.doc_id for d in db.search(query)) == [2, 5]


def test_explicit_id_insert_served_without_rescan():
    db = TinyDB(storage=MemoryStorage)
    table = db.table('t')
    table.insert(Document({'int': 1}, doc_id=9))
    other = where('int') == 2
    query = where('int') == 1
    table.search(query)
    table.search(other)

    table.insert(Document({'int': 1}, doc_id=3))
    table._read_table = lambda: {}

    assert sorted(d.doc_id for d in table.search(query)) == [3, 9]
    assert table.search(other) == []
