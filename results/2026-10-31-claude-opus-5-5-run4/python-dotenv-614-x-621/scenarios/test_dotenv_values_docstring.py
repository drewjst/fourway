import inspect

from dotenv.main import dotenv_values


def test_dotenv_values_documents_interpolate():
    doc = inspect.getdoc(dotenv_values)
    assert doc is not None
    line = "interpolate: Whether to interpolate variables using POSIX variable expansion."
    assert doc.count(line) == 1
    verbose_pos = doc.index("verbose: Whether to output a warning")
    interp_pos = doc.index(line)
    encoding_pos = doc.index("encoding: Encoding to be used")
    assert verbose_pos < interp_pos < encoding_pos
