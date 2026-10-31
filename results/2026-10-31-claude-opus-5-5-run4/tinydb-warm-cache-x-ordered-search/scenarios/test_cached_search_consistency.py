from tinydb import TinyDB, where
from tinydb.storages import MemoryStorage
from tinydb.table import Document


def _ids(docs):
    return [d.doc_id for d in docs]


def test_cached_result_equals_fresh_result_after_explicit_id_insert():
    db = TinyDB(storage=MemoryStorage)
    db.insert(Document({'int': 1}, doc_id=8))
    db.insert(Document({'int': 1}, doc_id=6))
    query = where('int') == 1
    db.search(query)

    db.insert(Document({'int': 1}, doc_id=4))

    served = db.search(query)
    db.clear_cache()
    fresh = db.search(query)

    assert _ids(served) == _ids(fresh)
    assert served == fresh


def test_cached_result_equals_fresh_result_after_auto_id_insert():
    db = TinyDB(storage=MemoryStorage)
    db.insert(Document({'int': 1}, doc_id=3))
    db.insert({'int': 2})
    query = where('int') == 1
    db.search(query)

    db.insert({'int': 1})

    served = db.search(query)
    db.clear_cache()
    fresh = db.search(query)

    assert _ids(served) == _ids(fresh)
    assert len(served) == 2
