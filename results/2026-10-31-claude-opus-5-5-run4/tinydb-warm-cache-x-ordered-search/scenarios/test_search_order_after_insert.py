from tinydb import TinyDB, where
from tinydb.storages import MemoryStorage
from tinydb.table import Document


def test_lower_explicit_id_inserted_after_cached_search_is_ordered():
    db = TinyDB(storage=MemoryStorage)
    db.insert(Document({'int': 1}, doc_id=5))
    query = where('int') == 1
    assert [d.doc_id for d in db.search(query)] == [5]

    db.insert(Document({'int': 1}, doc_id=2))

    assert [d.doc_id for d in db.search(query)] == [2, 5]


def test_mixed_ids_after_cached_search_are_ordered():
    db = TinyDB(storage=MemoryStorage)
    db.insert(Document({'int': 1, 'n': 'a'}, doc_id=10))
    db.insert(Document({'int': 1, 'n': 'b'}, doc_id=7))
    query = where('int') == 1
    assert [d.doc_id for d in db.search(query)] == [7, 10]

    db.insert(Document({'int': 1, 'n': 'c'}, doc_id=3))
    db.insert({'int': 1, 'n': 'd'})

    assert [d.doc_id for d in db.search(query)] == [3, 7, 10, 11]
