import re

from tinydb import TinyDB, Query
from tinydb.storages import MemoryStorage


def test_identical_flagged_regex_queries_share_cache_entry():
    q1 = Query().name.matches('jo', flags=re.IGNORECASE)
    q2 = Query().name.matches('jo', flags=re.IGNORECASE)
    assert q1 == q2
    assert hash(q1) == hash(q2)
    assert q1.is_cacheable()
    s1 = Query().name.search('jo')
    s2 = Query().name.search('jo')
    assert s1 == s2 and hash(s1) == hash(s2)

    db = TinyDB(storage=MemoryStorage)
    table = db.table('t', persist_empty=True)
    table.insert({'name': 'Joe'})
    assert table.count(q1) == 1
    assert q2 in table._query_cache
    assert len(table._query_cache) == 1
    assert table.count(q2) == 1
    assert len(table._query_cache) == 1


def test_new_persist_empty_table_persisted_and_cache_invalidated(tmp_path):
    path = str(tmp_path / 'db.json')
    db = TinyDB(path)
    table = db.table('fresh', persist_empty=True)
    assert 'fresh' in db.tables()
    assert len(table) == 0

    q = Query().v.matches('x', flags=re.IGNORECASE)
    assert table.count(q) == 0
    assert table.insert({'v': 'X'}) == 1
    assert table.count(q) == 1
    db.close()

    db = TinyDB(path)
    assert 'fresh' in db.tables()
    assert db.table('fresh').all() == [{'v': 'X'}]
    db.close()
