import pytest

from tomlkit import parse
from tomlkit.exceptions import UnexpectedCharError


@pytest.mark.parametrize(
    "content",
    [
        "[a.b]\nx = [, 1]\n[a]\n[a.c]\n",
        "[a.b]\nx = [1, , 2]\n[a]\n[a.c]\n",
        "[a.b]\nx = []\n[a]\ny = [1 2]\n",
    ],
)
def test_malformed_arrays_still_raise(content: str) -> None:
    with pytest.raises(UnexpectedCharError):
        parse(content)
