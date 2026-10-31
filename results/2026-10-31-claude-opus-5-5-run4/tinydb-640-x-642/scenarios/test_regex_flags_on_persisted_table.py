import re

from tinydb import TinyDB, Query
from tinydb.storages import MemoryStorage


def test_matches_flags_isolated_on_persist_empty_table():
    db = TinyDB(storage=MemoryStorage)
    table = db.table('people', persist_empty=True)
    assert 'people' in db.tables()

    table.insert({'name': 'John'})
    table.insert({'name': 'johnny'})

    insensitive = Query().name.matches('john', flags=re.IGNORECASE)
    sensitive = Query().name.matches('john')

    assert sorted(d['name'] for d in table.search(insensitive)) == ['John', 'johnny']
    assert [d['name'] for d in table.search(sensitive)] == ['johnny']
    # and again, both served from cache now
    assert sorted(d['name'] for d in table.search(insensitive)) == ['John', 'johnny']
    assert [d['name'] for d in table.search(sensitive)] == ['johnny']


def test_search_flags_isolated_on_persist_empty_table_reverse_order(tmp_path):
    path = str(tmp_path / 'db.json')
    db = TinyDB(path)
    table = db.table('people', persist_empty=True)
    table.insert({'name': 'Mr SMITH'})
    table.insert({'name': 'mrs smith'})

    sensitive = Query().name.search('smith')
    insensitive = Query().name.search('smith', flags=re.IGNORECASE)

    assert [d['name'] for d in table.search(sensitive)] == ['mrs smith']
    assert sorted(d['name'] for d in table.search(insensitive)) == ['Mr SMITH', 'mrs smith']
    assert table.count(sensitive) == 1
    assert table.count(insensitive) == 2
    db.close()
