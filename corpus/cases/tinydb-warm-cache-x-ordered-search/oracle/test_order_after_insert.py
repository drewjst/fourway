from tinydb import TinyDB, where
from tinydb.storages import MemoryStorage
from tinydb.table import Document


def test_a_cached_search_stays_in_id_order_after_an_insert():
    db = TinyDB(storage=MemoryStorage)
    db.insert(Document({'int': 1}, doc_id=5))
    query = where('int') == 1
    db.search(query)

    db.insert(Document({'int': 1}, doc_id=2))

    assert [doc.doc_id for doc in db.search(query)] == [2, 5]
