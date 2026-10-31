import re

from tinydb import TinyDB, Query


def _seed(path):
    db = TinyDB(path)
    t = db.table('people')
    t.insert({'name': 'John'})
    t.insert({'name': 'johnny'})
    db.close()


def test_reopen_with_persist_empty_keeps_docs_for_regex_search(tmp_path):
    path = str(tmp_path / 'db.json')
    _seed(path)

    db = TinyDB(path)
    table = db.table('people', persist_empty=True)
    assert len(table) == 2
    q = Query().name.matches('JOHN', flags=re.IGNORECASE)
    assert sorted(d['name'] for d in table.search(q)) == ['John', 'johnny']
    db.close()

    db = TinyDB(path)
    assert sorted(d['name'] for d in db.table('people').all()) == ['John', 'johnny']
    db.close()


def test_reopen_with_persist_empty_then_insert_updates_cached_search(tmp_path):
    path = str(tmp_path / 'db.json')
    _seed(path)

    db = TinyDB(path)
    table = db.table('people', persist_empty=True)
    q = Query().name.search('john', flags=re.IGNORECASE)
    assert table.count(q) == 2
    new_id = table.insert({'name': 'JOHNSON'})
    assert new_id == 3
    assert table.count(q) == 3
    db.close()
