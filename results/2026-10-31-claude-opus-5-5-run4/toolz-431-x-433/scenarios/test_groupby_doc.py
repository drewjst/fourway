import toolz
from toolz.itertoolz import groupby


def test_groupby_doc_mentions_itertools_groupby():
    doc = groupby.__doc__
    assert doc is not None
    assert 'Not to be confused with ``itertools.groupby``' in doc
    # The public alias exposes the same docstring.
    assert 'itertools.groupby' in toolz.groupby.__doc__
