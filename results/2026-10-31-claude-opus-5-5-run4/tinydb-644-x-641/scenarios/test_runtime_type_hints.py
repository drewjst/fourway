import inspect
import typing

from tinydb import operations
from tinydb.queries import Query
from tinydb.table import Table


def test_add_and_query_test_annotations():
    ann = inspect.signature(operations.add).parameters['n'].annotation
    assert str in typing.get_args(ann)

    func_ann = inspect.signature(Query.test).parameters['func'].annotation
    args = typing.get_args(func_ann)
    assert args, func_ann
    assert args[0] is Ellipsis
    assert args[-1] is bool


def test_docstrings_describe_runtime_behavior():
    assert 'insertion order' in Table.get.__doc__
    assert 'field value' in Query.test.__doc__
