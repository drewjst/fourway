from tinydb import TinyDB, where
from tinydb.storages import MemoryStorage
from tinydb.operations import delete


def test_documented_delete_example_and_cache_invalidation():
    db = TinyDB(storage=MemoryStorage)
    db.insert_multiple([{'foo': 2, 'k': 'a'}, {'foo': 3, 'k': 'b'}])
    q = where('foo') == 2
    assert len(db.search(q)) == 1
    assert len(db.search(q)) == 1  # cached hit
    db.update(delete('foo'), where('foo') == 2)
    assert db.search(q) == []
    assert db.get(where('k') == 'a') == {'k': 'a'}
    assert db.get(where('k') == 'b') == {'foo': 3, 'k': 'b'}
