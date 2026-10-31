import tinydb.operations as ops


def test_operations_docstring_example_is_balanced():
    doc = ops.__doc__
    assert "db.update(delete('foo'), where('foo') == 2)" in doc
    for line in doc.splitlines():
        if line.startswith('>>>'):
            assert line.count('(') == line.count(')'), line
