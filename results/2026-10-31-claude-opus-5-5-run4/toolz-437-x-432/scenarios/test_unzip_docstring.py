from toolz.sandbox.core import unzip


def test_unzip_docstring_describes_infinite_outer_sequence():
    doc = unzip.__doc__
    assert 'can handle an infinite sequence ``seq``' in doc
    assert 'The inner sequence cannot be infinite' in doc
    assert 'The top level sequence cannot be infinite' not in doc
    assert 'finite sequence of infinite sequences.\n\n    Caveats' not in doc
