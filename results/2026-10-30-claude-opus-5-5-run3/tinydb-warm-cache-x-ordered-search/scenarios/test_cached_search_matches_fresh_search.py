from tinydb import TinyDB, where
from tinydb.storages import MemoryStorage, JSONStorage
from tinydb.table import Document


def _ids(docs):
    return [d.doc_id for d in docs]


def test_cached_equals_fresh_after_explicit_id_insert_memory():
    db = TinyDB(storage=MemoryStorage)
    table = db.table('t')
    table.insert(Document({'int': 1}, doc_id=10))
    query = where('int') == 1
    table.search(query)

    table.insert(Document({'int': 1}, doc_id=4))
    table.insert({'int': 1})

    cached = table.search(query)
    table.clear_cache()
    fresh = table.search(query)

    assert _ids(cached) == _ids(fresh)
    assert cached == fresh


def test_cached_equals_fresh_after_explicit_id_insert_json(tmp_path):
    db = TinyDB(str(tmp_path / 'db.json'), storage=JSONStorage)
    try:
        db.insert(Document({'int': 1, 'c': 'x'}, doc_id=6))
        db.insert(Document({'int': 2}, doc_id=8))
        query = where('int') == 1
        db.search(query)

        db.insert(Document({'int': 1, 'c': 'y'}, doc_id=1))

        cached = db.search(query)
        db.clear_cache()
        fresh = db.search(query)

        assert _ids(cached) == _ids(fresh)
        assert cached == fresh
    finally:
        db.close()
