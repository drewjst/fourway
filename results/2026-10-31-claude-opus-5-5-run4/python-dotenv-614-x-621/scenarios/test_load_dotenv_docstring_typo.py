import inspect

from dotenv.main import load_dotenv


def test_load_dotenv_docstring_uses_its():
    doc = inspect.getdoc(load_dotenv)
    assert doc is not None
    assert "with its default parameters" in doc
    assert "it's default" not in doc
    assert doc.count("find_dotenv()` is used to find the") == 1
    assert doc.index("Returns:") < doc.index("with its default parameters")
