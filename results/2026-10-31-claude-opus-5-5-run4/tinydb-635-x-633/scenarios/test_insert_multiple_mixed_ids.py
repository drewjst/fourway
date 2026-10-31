from tinydb import TinyDB, where
from tinydb.storages import MemoryStorage, JSONStorage
from tinydb.table import Document


def test_mixed_batch_with_warm_query_cache():
    db = TinyDB(storage=MemoryStorage)
    q_auto = where('tag') == 'auto'
    q_all = where('tag').exists()

    # Warm the query cache with empty results
    assert db.search(q_auto) == []
    assert db.search(q_all) == []

    ids = db.insert_multiple([
        Document({'tag': 'explicit'}, 1),
        {'tag': 'auto'},
    ])

    assert ids == [1, 2]
    assert len(db) == 2
    assert db.get(doc_id=1) == {'tag': 'explicit'}
    assert db.get(doc_id=2) == {'tag': 'auto'}

    found = db.search(q_auto)
    assert len(found) == 1
    assert found[0].doc_id == 2
    assert len(db.search(q_all)) == 2
    # Served from cache the second time, still correct
    assert len(db.search(q_all)) == 2


def test_mixed_batch_after_primed_next_id_json(tmp_path):
    path = str(tmp_path / 'db.json')
    with TinyDB(path, storage=JSONStorage) as db:
        assert db.insert({'a': 1}) == 1  # primes _next_id to 2
        assert db.count(where('a').exists()) == 1  # cache an entry

        ids = db.insert_multiple([
            Document({'b': 1}, 2),
            {'c': 1},
        ])
        assert ids == [2, 3]
        assert len(db) == 3
        assert db.get(doc_id=2) == {'b': 1}
        assert db.get(doc_id=3) == {'c': 1}
        assert db.count(where('a').exists()) == 1

        assert db.insert({'d': 1}) == 4
        assert len(db) == 4
