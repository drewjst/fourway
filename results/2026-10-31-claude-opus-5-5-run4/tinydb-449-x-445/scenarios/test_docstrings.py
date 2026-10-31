from tinydb import operations
from tinydb.queries import QueryInstance


def test_subtract_docstring_spelling():
    doc = operations.subtract.__doc__
    assert doc is not None
    assert 'Subtract' in doc
    assert 'Substract' not in doc


def test_query_call_docstring_spelling():
    doc = QueryInstance.__call__.__doc__
    assert doc is not None
    assert 'Whether the value matches this query' in doc
    assert 'Wether' not in doc
    assert 'matchs' not in doc
