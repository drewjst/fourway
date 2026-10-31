import os

from tinydb import TinyDB, where
from tinydb.operations import delete, increment
from tinydb.storages import JSONStorage


def test_nested_create_dirs_and_transform_updates_persist(tmp_path):
    path = str(tmp_path / 'a' / 'b' / 'db.json')
    assert not os.path.exists(os.path.dirname(path))

    db = TinyDB(path, create_dirs=True, storage=JSONStorage)
    db.insert_multiple([{'k': 1, 'tmp': 'x'}, {'k': 2, 'tmp': 'y'}])
    db.update(delete('tmp'), where('k') == 1)
    db.update(increment('k'), where('k') == 2)
    db.close()

    assert os.path.exists(path)
    db2 = TinyDB(path, create_dirs=True, storage=JSONStorage)
    assert db2.all() == [{'k': 1}, {'k': 3, 'tmp': 'y'}]
    db2.close()


def test_absolute_path_without_create_dirs_still_works(tmp_path):
    path = str(tmp_path / 'flat.json')
    db = TinyDB(path, storage=JSONStorage)

    def mutate(doc):
        doc['v'] = doc['v'] * 10

    doc_id = db.insert({'v': 2})
    assert db.update(mutate, doc_ids=[doc_id]) == [doc_id]
    db.close()

    db2 = TinyDB(path, storage=JSONStorage)
    assert db2.get(doc_id=doc_id) == {'v': 20}
    db2.close()
