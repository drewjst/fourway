from tenacity import BaseRetrying


def test_fixed_docstrings_present():
    stats_doc = BaseRetrying.statistics.__doc__ or ""
    wraps_doc = BaseRetrying.wraps.__doc__ or ""
    if not stats_doc or not wraps_doc:
        import pytest

        pytest.skip("docstrings stripped")
    assert "their existence" in stats_doc
    assert "their own view" in stats_doc
    assert "somewhat" in stats_doc
    assert "there existence" not in stats_doc
    assert "A function to wrap for retrying." in wraps_doc
