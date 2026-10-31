from tinydb import TinyDB, where
from tinydb.storages import MemoryStorage
from tinydb.table import Document


def test_search_after_explicit_lower_id_insert_is_id_ordered():
    db = TinyDB(storage=MemoryStorage)
    db.insert(Document({'int': 1}, doc_id=5))
    query = where('int') == 1
    assert [d.doc_id for d in db.search(query)] == [5]

    db.insert(Document({'int': 1}, doc_id=2))

    assert [d.doc_id for d in db.search(query)] == [2, 5]


def test_mixed_auto_and_explicit_inserts_after_cached_search():
    db = TinyDB(storage=MemoryStorage)
    table = db.table('t')
    table.insert({'int': 1})
    table.insert(Document({'int': 1}, doc_id=7))
    query = where('int') == 1
    assert [d.doc_id for d in table.search(query)] == [1, 7]

    table.insert(Document({'int': 1}, doc_id=3))
    new_id = table.insert({'int': 1})
    assert new_id == 8

    assert [d.doc_id for d in table.search(query)] == [1, 3, 7, 8]
