import tenacity
from tenacity import wait as tenacity_wait


def _normalized(doc):
    return " ".join((doc or "").split())


def test_docstring_describes_additive_jitter():
    doc = _normalized(tenacity_wait.wait_exponential_jitter.__doc__)
    assert "min(initial * 2**n + random.uniform(0, jitter), maximum)" in doc
    assert "initial * (2**n + random.uniform(0, jitter))" not in doc


def test_docstring_visible_via_package_namespace():
    cls = tenacity.wait_exponential_jitter
    assert cls is tenacity_wait.wait_exponential_jitter
    doc = _normalized(cls.__doc__)
    assert "min(initial * 2**n + random.uniform(0, jitter), maximum)" in doc
