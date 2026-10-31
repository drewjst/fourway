import inspect

from dotenv.main import load_dotenv


def _doc():
    doc = inspect.getdoc(load_dotenv)
    assert doc is not None
    return doc


def test_load_dotenv_documents_interpolate_once_in_parameters():
    doc = _doc()
    line = "interpolate: Whether to interpolate variables using POSIX variable expansion."
    assert doc.count(line) == 1
    params_start = doc.index("Parameters:")
    returns_start = doc.index("Returns:")
    pos = doc.index(line)
    assert params_start < pos < returns_start


def test_load_dotenv_interpolate_between_override_and_encoding():
    doc = _doc()
    override_pos = doc.index("override: Whether to override")
    interp_pos = doc.index("interpolate: Whether to interpolate")
    encoding_pos = doc.index("encoding: Encoding to be used")
    assert override_pos < interp_pos < encoding_pos
