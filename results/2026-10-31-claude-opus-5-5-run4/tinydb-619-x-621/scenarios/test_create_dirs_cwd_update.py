import os

from tinydb import TinyDB, where
from tinydb.operations import delete
from tinydb.storages import JSONStorage, touch


def test_touch_bare_filename_with_create_dirs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    touch('plain.json', True)
    assert os.path.exists(tmp_path / 'plain.json')


def test_tinydb_bare_filename_create_dirs_update_transforms(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    db = TinyDB('some.json', create_dirs=True, storage=JSONStorage)
    doc_id = db.insert({'name': 'John', 'temp': True, 'other': 1})

    def remove_temp(doc):
        del doc['temp']

    assert db.update(remove_temp, where('name') == 'John') == [doc_id]
    db.update_multiple([(delete('other'), where('name') == 'John')])
    assert db.get(doc_id=doc_id) == {'name': 'John'}
    db.close()

    db2 = TinyDB('some.json', create_dirs=True, storage=JSONStorage)
    assert db2.all() == [{'name': 'John'}]
    db2.close()
